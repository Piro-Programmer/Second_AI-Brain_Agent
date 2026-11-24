import lib.config as config
import lib.db as db
from lib.embeddings import embed_text, cosine_similarity, text_hash

def process_unlinked(username: str = None):
    """Embed new or edited notes, then link every pair of notes above the similarity threshold."""
    username = username or config.get_user()
    print("Starting auto-linking pipeline...")

    notes = db.get_notes(username, processed=True)

    # Phase 1: embed notes that are new or whose text changed since the last run
    for note in notes:
        text_to_embed = f"{note['summary']}\n\n{note['content']}"
        current_hash = text_hash(text_to_embed)
        if note["embedding"] is None or note["embedded_text_hash"] != current_hash:
            print(f"Embedding note: {note['id']}")
            note["embedding"] = embed_text(text_to_embed)
            db.set_embedding(note["id"], note["embedding"], current_hash)

    # Phase 2: compare every pair once and store links on both notes
    links = {note["id"]: set(note["links"]) for note in notes}
    for i, a in enumerate(notes):
        for b in notes[i + 1:]:
            if b["id"] in links[a["id"]]:
                continue
            sim = cosine_similarity(a["embedding"], b["embedding"])
            if sim >= config.SIMILARITY_LINK_THRESHOLD:
                print(f"Match found! {a['id']} <-> {b['id']} (Score: {sim:.2f})")
                links[a["id"]].add(b["id"])
                links[b["id"]].add(a["id"])

    links_added = 0
    for note in notes:
        new_links = sorted(links[note["id"]])
        if new_links != sorted(note["links"]):
            links_added += len(new_links) - len(note["links"])
            db.set_links(note["id"], new_links)

    print(f"Auto-linking complete. Inserted {links_added} new links.")
    return links_added

if __name__ == "__main__":
    process_unlinked()
