import lib.config as config
import lib.db as db
from lib.llm import classify_content, LLMError

def main(username: str = None):
    """Classify every unprocessed note of a user into PARA with tags and a summary."""
    username = username or config.get_user()
    print("Starting classification pipeline...")

    processed_count = 0
    for note in db.get_notes(username, processed=False):
        print(f"Processing: {note['id']}")
        content = note["content"]

        if not content.strip():
            print(f"  Skipping {note['id']} (empty capture)")
            continue

        # Classify via LLM; leave the item unprocessed on failure so the next run retries it
        try:
            result = classify_content(content)
        except LLMError as e:
            print(f"  Skipping {note['id']} (LLM error: {e})")
            continue
        para = result.get("para", "Resources")
        tags = result.get("tags", [])
        if not isinstance(tags, list):
            tags = [str(tags)]
        summary = result.get("summary", "No summary.")

        db.set_classification(note["id"], para, tags, summary)
        print(f"  -> Classified as {para}: {summary}")
        processed_count += 1

    print(f"Classification complete. Processed {processed_count} new items.")
    return processed_count

if __name__ == "__main__":
    main()
