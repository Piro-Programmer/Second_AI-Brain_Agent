"""Forgot-password flow: email a short-lived 6-digit code, then let the user set a new password."""
import secrets
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage

from streamlit_authenticator.utilities import Hasher, Validator

import lib.config as config
import lib.db as db

CODE_MINUTES_VALID = 15
MAX_ATTEMPTS = 5
PASSWORD_RULES = ("8-20 characters with at least one uppercase letter, one lowercase letter, "
                  "one number and one special character (e.g. # @ !)")

# Same message whether or not the account exists, so the form can't be used to find accounts
GENERIC_SENT = "If an account matches, a reset code has been sent to its email address."


def email_configured() -> bool:
    return all(config.get_env_var(k) for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"))


def send_email(to: str, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = config.get_env_var("SMTP_FROM") or config.get_env_var("SMTP_USER")
    msg["To"] = to
    msg.set_content(body)
    host = config.get_env_var("SMTP_HOST")
    port = int(config.get_env_var("SMTP_PORT", 587))
    with smtplib.SMTP(host, port, timeout=20) as server:
        server.starttls()
        server.login(config.get_env_var("SMTP_USER"), config.get_env_var("SMTP_PASSWORD"))
        server.send_message(msg)


def request_reset(username_or_email: str) -> str:
    """Email a reset code to the matching account. Returns a message for the user."""
    if not email_configured():
        return "Password reset by email isn't set up on this server yet. Please contact the admin."
    user = db.find_user(username_or_email)
    if user is None:
        return GENERIC_SENT

    code = f"{secrets.randbelow(10**6):06d}"
    db.save_reset_code(user["username"], Hasher.hash(code), CODE_MINUTES_VALID)
    send_email(
        user["email"],
        "Your SecondSelf password reset code",
        f"Hi {user['first_name'] or user['username']},\n\n"
        f"Your password reset code is: {code}\n\n"
        f"It expires in {CODE_MINUTES_VALID} minutes. If you didn't ask for this, ignore this email; "
        f"your password stays the same.\n\n- SecondSelf",
    )
    return GENERIC_SENT


def confirm_reset(username_or_email: str, code: str, new_password: str,
                  repeat_password: str) -> tuple[bool, str]:
    """Check the code and set the new password. Returns (success, message)."""
    invalid = (False, "That code is invalid or has expired. Request a new one.")
    user = db.find_user(username_or_email)
    if user is None:
        return invalid
    username = user["username"]
    pending = db.get_reset_code(username)
    if pending is None or pending["expires_at"] < datetime.now(timezone.utc) \
            or pending["attempts"] >= MAX_ATTEMPTS:
        return invalid
    if not Hasher.check_pw(code.strip(), pending["code_hash"]):
        db.bump_reset_attempts(username)
        return invalid
    if new_password != repeat_password:
        return False, "The passwords don't match."
    if not Validator().validate_password(new_password):
        return False, f"Password must be {PASSWORD_RULES}."

    db.set_password_hash(username, Hasher.hash(new_password))
    db.clear_reset_code(username)
    return True, "Password changed. You can now log in with your new password."
