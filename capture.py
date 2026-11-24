import os
import sys
import argparse

import lib.config as config
import lib.db as db
from lib.parsers import fetch_link_content, extract_pdf_text

def capture_note(text: str, username: str = None) -> str:
    """Capture a plain text note; returns the new note id."""
    note_id = db.add_note(username or config.get_user(), text, source_type="note")
    print(f"Captured note: {note_id}")
    return note_id

def capture_link(url: str, username: str = None) -> str:
    """Capture content from a link."""
    content = fetch_link_content(url)
    md_content = f"# {content['title']}\n\n**URL:** {content['url']}\n\n{content['text']}"
    note_id = db.add_note(username or config.get_user(), md_content, source_type="link", url=url)
    print(f"Captured link: {note_id}")
    return note_id

def capture_file(file_path: str, username: str = None) -> str:
    """Capture a file, extracting text if it is a PDF or text file."""
    if not os.path.exists(file_path):
        print(f"Error: File not found -> {file_path}")
        sys.exit(1)

    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        extracted_text = extract_pdf_text(file_path)
    else:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                extracted_text = f.read()
        except Exception:
            extracted_text = f"Binary file captured: {os.path.basename(file_path)}"

    note_id = db.add_note(username or config.get_user(), extracted_text, source_type="file",
                          original_filename=os.path.basename(file_path))
    print(f"Captured file: {note_id}")
    return note_id

def list_captures(username: str = None):
    """List all captured items in the terminal."""
    notes = db.get_notes(username or config.get_user())
    if not notes:
        print("No captures found.")
        return

    print(f"\n--- Found {len(notes)} captures ---")
    for note in reversed(notes):
        info = f"[{note['created_at']:%Y-%m-%d %H:%M}] {note['source_type'].upper()}"
        if note["url"]:
            info += f" - {note['url']}"
        elif note["original_filename"]:
            info += f" - {note['original_filename']}"
        snippet = note["content"][:100].replace("\n", " ").strip()
        if len(note["content"]) > 100:
            snippet += "..."
        status = note["para"] if note["processed"] else "unprocessed"

        print(f"\n- ID:      {note['id']} ({status})")
        print(f"  Info:    {info}")
        print(f"  Preview: {snippet}")
    print("\n-------------------------------------")

def main():
    parser = argparse.ArgumentParser(description="SecondSelf Capture Pipeline")
    parser.add_argument("--user", type=str, default="default", help="Username to capture for")
    parser.add_argument("--note", type=str, help="Capture a text note")
    parser.add_argument("--link", type=str, help="Capture a URL")
    parser.add_argument("--file", type=str, help="Capture a file path")
    parser.add_argument("--list", action="store_true", help="List all captured items in the terminal")

    args = parser.parse_args()
    config.set_user(args.user)

    if args.list:
        list_captures()
    elif args.note:
        capture_note(args.note)
    elif args.link:
        capture_link(args.link)
    elif args.file:
        capture_file(args.file)
    else:
        print("Please provide --note, --link, --file, or --list. See --help for details.")

if __name__ == "__main__":
    main()
