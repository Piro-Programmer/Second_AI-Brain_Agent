"""Database storage for users, notes and password resets.

Uses DATABASE_URL (e.g. Supabase Postgres) when set, otherwise a local SQLite file,
so the same code runs on a laptop and on Streamlit Cloud without data being wiped.
"""
import json
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import numpy as np
from sqlalchemy import (Boolean, Column, DateTime, Integer, LargeBinary, MetaData, String,
                        Table, Text, create_engine, delete, func, insert, or_, select, update)

import lib.config as config

LOCAL_DB_PATH = "data/secondself.db"

metadata = MetaData()

users = Table(
    "users", metadata,
    Column("username", String(64), primary_key=True),
    Column("email", String(254), nullable=False, unique=True),
    Column("first_name", String(100), nullable=False, default=""),
    Column("last_name", String(100), nullable=False, default=""),
    Column("password_hash", String(255), nullable=False),
    Column("password_hint", String(255)),
    Column("roles", Text),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

notes = Table(
    "notes", metadata,
    Column("id", String(36), primary_key=True),
    Column("username", String(64), nullable=False, index=True),
    Column("source_type", String(16), nullable=False, default="note"),
    Column("url", Text),
    Column("original_filename", String(255)),
    Column("content", Text, nullable=False),
    Column("processed", Boolean, nullable=False, default=False),
    Column("para", String(16)),
    Column("tags", Text),
    Column("summary", Text),
    Column("links", Text),
    Column("embedding", LargeBinary),
    Column("embedded_text_hash", String(64)),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

password_resets = Table(
    "password_resets", metadata,
    Column("username", String(64), primary_key=True),
    Column("code_hash", String(255), nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("attempts", Integer, nullable=False, default=0),
)

settings = Table(
    "settings", metadata,
    Column("key", String(64), primary_key=True),
    Column("value", Text, nullable=False),
)

_engine = None


def _database_url() -> str:
    url = config.get_env_var("DATABASE_URL")
    if not url:
        os.makedirs(os.path.dirname(LOCAL_DB_PATH), exist_ok=True)
        return f"sqlite:///{LOCAL_DB_PATH}"
    # Supabase/Heroku hand out postgres:// URLs; SQLAlchemy needs the psycopg driver named
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


def get_engine():
    """Create the engine and tables once per process."""
    global _engine
    if _engine is None:
        _engine = create_engine(_database_url(), pool_pre_ping=True)
        metadata.create_all(_engine)
    return _engine


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    # SQLite returns naive datetimes even for timezone=True columns
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


# -----------------------------------------------------------------------------
# Settings
# -----------------------------------------------------------------------------
def get_or_create_setting(key: str, make_value) -> str:
    with get_engine().begin() as conn:
        value = conn.execute(select(settings.c.value).where(settings.c.key == key)).scalar()
        if value is None:
            value = make_value()
            conn.execute(insert(settings).values(key=key, value=value))
        return value


def get_cookie_key() -> str:
    """Stable secret for login cookies: from AUTH_COOKIE_KEY, else generated once and stored."""
    return config.get_env_var("AUTH_COOKIE_KEY") or get_or_create_setting(
        "auth_cookie_key", lambda: secrets.token_hex(32))


# -----------------------------------------------------------------------------
# Users
# -----------------------------------------------------------------------------
def load_credentials() -> dict:
    """All users in the {'usernames': {...}} shape streamlit-authenticator expects."""
    with get_engine().connect() as conn:
        rows = conn.execute(select(users)).mappings().all()
    return {"usernames": {
        r["username"]: {
            "email": r["email"],
            "first_name": r["first_name"],
            "last_name": r["last_name"],
            "password": r["password_hash"],
            "password_hint": r["password_hint"],
            "roles": json.loads(r["roles"]) if r["roles"] else None,
            "logged_in": False,
        }
        for r in rows
    }}


def save_user(username: str, data: dict) -> None:
    """Insert or update one user from a streamlit-authenticator credentials entry."""
    values = {
        "email": data.get("email", ""),
        "first_name": data.get("first_name", "") or "",
        "last_name": data.get("last_name", "") or "",
        "password_hash": data["password"],
        "password_hint": data.get("password_hint"),
        "roles": json.dumps(data["roles"]) if data.get("roles") else None,
    }
    with get_engine().begin() as conn:
        exists = conn.execute(select(users.c.username).where(users.c.username == username)).first()
        if exists:
            conn.execute(update(users).where(users.c.username == username).values(**values))
        else:
            conn.execute(insert(users).values(username=username, created_at=_now(), **values))


def sync_credentials(credentials: dict) -> None:
    """Persist any users added or changed in the in-memory credentials dict."""
    stored = load_credentials()["usernames"]
    for username, data in credentials["usernames"].items():
        old = stored.get(username)
        if old is None or any(old.get(k) != data.get(k) for k in
                              ("email", "first_name", "last_name", "password", "password_hint", "roles")):
            save_user(username, data)


def find_user(username_or_email: str):
    key = username_or_email.strip().lower()
    with get_engine().connect() as conn:
        return conn.execute(select(users).where(
            or_(func.lower(users.c.username) == key, func.lower(users.c.email) == key)
        )).mappings().first()


def set_password_hash(username: str, password_hash: str) -> None:
    with get_engine().begin() as conn:
        conn.execute(update(users).where(users.c.username == username)
                     .values(password_hash=password_hash))


def list_usernames() -> list[str]:
    with get_engine().connect() as conn:
        return list(conn.execute(select(users.c.username).order_by(users.c.username)).scalars())


# -----------------------------------------------------------------------------
# Password reset codes
# -----------------------------------------------------------------------------
def save_reset_code(username: str, code_hash: str, minutes_valid: int = 15) -> None:
    with get_engine().begin() as conn:
        conn.execute(delete(password_resets).where(password_resets.c.username == username))
        conn.execute(insert(password_resets).values(
            username=username, code_hash=code_hash,
            expires_at=_now() + timedelta(minutes=minutes_valid), attempts=0))


def get_reset_code(username: str):
    with get_engine().connect() as conn:
        row = conn.execute(select(password_resets)
                           .where(password_resets.c.username == username)).mappings().first()
    if row is None:
        return None
    return {**row, "expires_at": _aware(row["expires_at"])}


def bump_reset_attempts(username: str) -> None:
    with get_engine().begin() as conn:
        conn.execute(update(password_resets).where(password_resets.c.username == username)
                     .values(attempts=password_resets.c.attempts + 1))


def clear_reset_code(username: str) -> None:
    with get_engine().begin() as conn:
        conn.execute(delete(password_resets).where(password_resets.c.username == username))


# -----------------------------------------------------------------------------
# Notes
# -----------------------------------------------------------------------------
def _note_dict(r) -> dict:
    return {
        "id": r["id"],
        "username": r["username"],
        "source_type": r["source_type"],
        "url": r["url"],
        "original_filename": r["original_filename"],
        "content": r["content"],
        "processed": bool(r["processed"]),
        "para": r["para"] or "Resources",
        "tags": json.loads(r["tags"]) if r["tags"] else [],
        "summary": r["summary"] or "Untitled Note",
        "links": json.loads(r["links"]) if r["links"] else [],
        "embedding": (np.frombuffer(r["embedding"], dtype=np.float32)
                      if r["embedding"] is not None else None),
        "embedded_text_hash": r["embedded_text_hash"],
        "created_at": _aware(r["created_at"]),
    }


def add_note(username: str, content: str, source_type: str = "note", url: str = None,
             original_filename: str = None, note_id: str = None, created_at: datetime = None,
             para: str = None, tags: list = None, summary: str = None) -> str:
    note_id = note_id or str(uuid.uuid4())
    processed = para is not None
    with get_engine().begin() as conn:
        conn.execute(insert(notes).values(
            id=note_id, username=username, source_type=source_type, url=url,
            original_filename=original_filename, content=content, processed=processed,
            para=para, tags=json.dumps(tags) if tags is not None else None, summary=summary,
            links=json.dumps([]), created_at=created_at or _now()))
    return note_id


def get_notes(username: str, processed: bool = None) -> list[dict]:
    query = select(notes).where(notes.c.username == username).order_by(notes.c.created_at)
    if processed is not None:
        query = query.where(notes.c.processed == processed)
    with get_engine().connect() as conn:
        return [_note_dict(r) for r in conn.execute(query).mappings()]


def note_exists(note_id: str) -> bool:
    with get_engine().connect() as conn:
        return conn.execute(select(notes.c.id).where(notes.c.id == note_id)).first() is not None


def set_classification(note_id: str, para: str, tags: list, summary: str) -> None:
    with get_engine().begin() as conn:
        conn.execute(update(notes).where(notes.c.id == note_id).values(
            processed=True, para=para, tags=json.dumps(tags), summary=summary))


def set_embedding(note_id: str, vector: np.ndarray, text_hash: str) -> None:
    with get_engine().begin() as conn:
        conn.execute(update(notes).where(notes.c.id == note_id).values(
            embedding=np.asarray(vector, dtype=np.float32).tobytes(),
            embedded_text_hash=text_hash))


def set_links(note_id: str, links: list[str]) -> None:
    with get_engine().begin() as conn:
        conn.execute(update(notes).where(notes.c.id == note_id).values(links=json.dumps(links)))


def delete_note(username: str, note_id: str) -> None:
    with get_engine().begin() as conn:
        conn.execute(delete(notes).where(notes.c.id == note_id, notes.c.username == username))
        # Drop dangling links to the deleted note
        for row in conn.execute(select(notes.c.id, notes.c.links)
                                .where(notes.c.username == username)).mappings():
            links = json.loads(row["links"]) if row["links"] else []
            if note_id in links:
                conn.execute(update(notes).where(notes.c.id == row["id"]).values(
                    links=json.dumps([l for l in links if l != note_id])))
