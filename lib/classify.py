import os
import json
from datetime import datetime
import lib.config as config
from lib.io import ensure_dir, write_json
from lib.llm import classify_content

INDEX_FILE = "data/index.json"

def load_index() -> dict:
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"raw_processed": []}

def save_index(index: dict):
    ensure_dir(config.DATA_DIR)
    write_json(index, INDEX_FILE)

def main():
    print("Starting classification pipeline...")
    ensure_dir(config.WIKI_DIR)
    for cat in config.PARA_CATEGORIES:
        ensure_dir(os.path.join(config.WIKI_DIR, cat))
        
    index = load_index()
    processed_ids = set(index.get("raw_processed", []))
    
    if not os.path.exists(config.RAW_DIR):
        print(f"Directory {config.RAW_DIR} does not exist.")
        return
        
    folders = sorted([f for f in os.listdir(config.RAW_DIR) if os.path.isdir(os.path.join(config.RAW_DIR, f))])
    
    processed_count = 0
    for folder in folders:
        if folder in processed_ids:
            continue
            
        print(f"Processing: {folder}")
        folder_path = os.path.join(config.RAW_DIR, folder)
        content_path = os.path.join(folder_path, "content.md")
        meta_path = os.path.join(folder_path, "meta.json")
        
        if not os.path.exists(content_path) or not os.path.exists(meta_path):
            print(f"  Skipping {folder} (missing content.md or meta.json)")
            continue
            
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
            
        with open(content_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            
        # Classify via LLM
        result = classify_content(content)
        para = result.get("para", "Resources")
        tags = result.get("tags", [])
        summary = result.get("summary", "No summary.")
        
        # Write to wiki/{PARA}/{id}.md
        wiki_filename = f"{folder}.md"
        wiki_path = os.path.join(config.WIKI_DIR, para, wiki_filename)
        
        # Construct Markdown with Frontmatter
        frontmatter = [
            "---",
            f"id: {meta.get('id')}",
            f"raw_id: {folder}",
            f"para: {para}",
            f"tags: {json.dumps(tags)}",
            f"summary: {json.dumps(summary)}",
            f"created: {meta.get('timestamp')}",
            "links: []",
            "---",
            "",
            content
        ]
        
        with open(wiki_path, "w", encoding="utf-8") as f:
            f.write("\n".join(frontmatter))
            
        print(f"  -> Classified as {para}: {summary}")
        
        processed_ids.add(folder)
        index["raw_processed"] = list(processed_ids)
        save_index(index)
        processed_count += 1
        
    print(f"Classification complete. Processed {processed_count} new items.")

if __name__ == "__main__":
    main()
