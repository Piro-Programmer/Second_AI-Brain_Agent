import os
import sys
import uuid
import shutil
import argparse
from datetime import datetime

import lib.config as config
from lib.io import write_json, ensure_dir
from lib.parsers import fetch_link_content, extract_pdf_text, detect_source_type

def generate_capture_id() -> tuple[str, str, str]:
    """Generate folder path for a capture, full_uuid, and iso_timestamp."""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    iso_timestamp = now.isoformat()
    full_uuid = str(uuid.uuid4())
    short_uuid = full_uuid[:8]
    
    folder_name = f"{date_str}_{short_uuid}"
    folder_path = os.path.join(config.RAW_DIR, folder_name)
    ensure_dir(folder_path)
    return folder_path, full_uuid, iso_timestamp

def capture_note(text: str) -> str:
    """Capture a plain text note."""
    folder_path, full_uuid, iso_timestamp = generate_capture_id()
    content_path = os.path.join(folder_path, "content.md")
    
    with open(content_path, "w", encoding="utf-8") as f:
        f.write(text)
        
    meta = {
        "id": full_uuid,
        "timestamp": iso_timestamp,
        "source_type": "note",
        "original_filename": None
    }
    write_json(meta, os.path.join(folder_path, "meta.json"))
    print(f"Captured note: {content_path}")
    return content_path

def capture_link(url: str) -> str:
    """Capture content from a link."""
    folder_path, full_uuid, iso_timestamp = generate_capture_id()
    content_path = os.path.join(folder_path, "content.md")
    
    content = fetch_link_content(url)
    md_content = f"# {content['title']}\n\n**URL:** {content['url']}\n\n{content['text']}"
    
    with open(content_path, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    meta = {
        "id": full_uuid,
        "timestamp": iso_timestamp,
        "source_type": "link",
        "original_filename": None,
        "url": url
    }
    write_json(meta, os.path.join(folder_path, "meta.json"))
    print(f"Captured link: {content_path}")
    return content_path

def capture_file(file_path: str) -> str:
    """Capture a file, extracting text if it is a PDF or text file."""
    if not os.path.exists(file_path):
        print(f"Error: File not found -> {file_path}")
        sys.exit(1)
        
    folder_path, full_uuid, iso_timestamp = generate_capture_id()
    content_path = os.path.join(folder_path, "content.md")
    
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    # Save original copy inside the folder
    orig_dest = os.path.join(folder_path, f"original{ext}")
    shutil.copy2(file_path, orig_dest)
    
    extracted_text = ""
    if ext == ".pdf":
        extracted_text = extract_pdf_text(file_path)
    else:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                extracted_text = f.read()
        except Exception:
            extracted_text = f"Binary file captured: {os.path.basename(file_path)}"
            
    with open(content_path, "w", encoding="utf-8") as f:
        f.write(extracted_text)
            
    meta = {
        "id": full_uuid,
        "timestamp": iso_timestamp,
        "source_type": "file",
        "original_filename": os.path.basename(file_path)
    }
    write_json(meta, os.path.join(folder_path, "meta.json"))
    print(f"Captured file: {content_path}")
    return content_path

def list_captures():
    """List all captured items in the terminal."""
    if not os.path.exists(config.RAW_DIR):
        print("No captures found.")
        return
        
    folders = sorted([f for f in os.listdir(config.RAW_DIR) if os.path.isdir(os.path.join(config.RAW_DIR, f))], reverse=True)
    if not folders:
        print("No captures found.")
        return
        
    print(f"\n--- Found {len(folders)} captures in raw/ ---")
    for folder in folders:
        meta_path = os.path.join(config.RAW_DIR, folder, "meta.json")
        content_path = os.path.join(config.RAW_DIR, folder, "content.md")
        if os.path.exists(meta_path):
            import json
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            
            info = f"[{meta['timestamp'][:16].replace('T', ' ')}] {meta['source_type'].upper()}"
            if meta.get("url"):
                info += f" - {meta['url']}"
            elif meta.get("original_filename"):
                info += f" - {meta['original_filename']}"
            
            # Read a small snippet of the content
            snippet = ""
            if os.path.exists(content_path):
                with open(content_path, "r", encoding="utf-8", errors="ignore") as f:
                    snippet = f.read(100).replace('\n', ' ').strip()
                    if len(snippet) == 100:
                        snippet += "..."
                
            print(f"\n- Folder:  {folder}")
            print(f"  Info:    {info}")
            print(f"  Preview: {snippet}")
    print("\n-------------------------------------")

def main():
    parser = argparse.ArgumentParser(description="SecondSelf Capture Pipeline")
    parser.add_argument("--note", type=str, help="Capture a text note")
    parser.add_argument("--link", type=str, help="Capture a URL")
    parser.add_argument("--file", type=str, help="Capture a file path")
    parser.add_argument("--list", action="store_true", help="List all captured items in the terminal")
    
    args = parser.parse_args()
    
    ensure_dir(config.RAW_DIR)
    
    if args.list:
        list_captures()
    elif args.note:
        capture_note(args.note)
    elif args.link:
        capture_link(args.link)
    elif args.file:
        capture_file(args.file)
    else:
        # If no arguments, try reading from stdin or prompting
        print("Please provide --note, --link, --file, or --list. See --help for details.")
        
if __name__ == "__main__":
    main()
