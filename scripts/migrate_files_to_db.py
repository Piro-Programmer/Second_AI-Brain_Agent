"""One-time import of the old file storage (users.yaml + users/<name>/raw|wiki) into the database.

Run from the project root:
    python scripts/migrate_files_to_db.py
Point DATABASE_URL at Supabase first to import into the cloud database instead of local SQLite.
Safe to run twice: users are upserted and notes that already exist are skipped.
"""
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import frontmatter
import yaml

import lib.db as db

WIKILINK_LINE = re.compile(r"^\s*\[\[[^\]]+\]\]\s*$", re.MULTILINE)


def parse_time(value) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value))
        except ValueError:
            dt = datetime.now()
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def migrate_users(path: str = "users.yaml") -> None:
    if not os.path.exists(path):
        print(f"No {path}; skipping users.")
        return
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    for username, data in (cfg.get("credentials", {}).get("usernames") or {}).items():
        db.save_user(username.lower(), data)
        print(f"User imported: {username}")


def migrate_notes(username: str, base: str) -> None:
    imported = skipped = 0
    wiki_ids = set()
    old_links = {}

    # Processed notes: wiki/<PARA>/*.md with frontmatter
    for path in glob.glob(os.path.join(base, "wiki", "**", "*.md"), recursive=True):
        post = frontmatter.load(path)
        note_id = str(post.get("id") or "").strip()
        if not note_id or not post.content.strip():
            continue
        wiki_ids.add(note_id)
        if db.note_exists(note_id):
            skipped += 1
            continue
        # Links now live in their own column, so drop the [[id]] lines auto-linking appended
        content = WIKILINK_LINE.sub("", post.content).rstrip()
        tags = post.get("tags") or []
        db.add_note(username, content, note_id=note_id, created_at=parse_time(post.get("created")),
                    para=post.get("para", "Resources"),
                    tags=tags if isinstance(tags, list) else [str(tags)],
                    summary=post.get("summary") or "Untitled Note")
        old_links[note_id] = [str(l) for l in (post.get("links") or [])]
        imported += 1

    # Captures never processed: raw/<folder>/content.md + meta.json not in wiki
    for folder in glob.glob(os.path.join(base, "raw", "*")):
        meta_path, content_path = os.path.join(folder, "meta.json"), os.path.join(folder, "content.md")
        if not (os.path.exists(meta_path) and os.path.exists(content_path)):
            continue
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
        note_id = meta.get("id")
        if not note_id or note_id in wiki_ids or db.note_exists(note_id):
            continue
        with open(content_path, encoding="utf-8", errors="ignore") as f:
            content = f.read()
        if not content.strip():
            continue
        db.add_note(username, content, source_type=meta.get("source_type", "note"),
                    url=meta.get("url"), original_filename=meta.get("original_filename"),
                    note_id=note_id, created_at=parse_time(meta.get("timestamp")))
        imported += 1

    for note_id, links in old_links.items():
        valid = [l for l in links if l in wiki_ids]
        if valid:
            db.set_links(note_id, valid)

    print(f"{username}: imported {imported} note(s), skipped {skipped} already in the database")


def main():
    migrate_users()
    for base in sorted(glob.glob(os.path.join("users", "*"))):
        if os.path.isdir(base):
            migrate_notes(os.path.basename(base).lower(), base)
    print("Done. Click Process & Link once per user to rebuild embeddings.")


if __name__ == "__main__":
    main()
