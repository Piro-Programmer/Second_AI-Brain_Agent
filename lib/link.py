import os
import glob
import json
import numpy as np
import frontmatter
import lib.config as config
from lib.embeddings import embed_text, cosine_similarity, load_embeddings, save_embeddings

EMBEDDINGS_FILE = os.path.join(config.DATA_DIR, "embeddings.pkl")

def get_all_wiki_notes():
    search_pattern = os.path.join(config.WIKI_DIR, "**", "*.md")
    return glob.glob(search_pattern, recursive=True)

def process_unlinked():
    print("Starting auto-linking pipeline...")
    
    # Load existing embeddings
    embeddings_db = load_embeddings(EMBEDDINGS_FILE)
    notes = get_all_wiki_notes()
    
    new_embeddings_added = False
    notes_data = {}
    
    # Phase 1: Embed all notes
    for note_path in notes:
        post = frontmatter.load(note_path)
        note_id = post.get("id")
        
        if not note_id:
            continue
            
        summary = post.get("summary", "")
        content = post.content
        
        text_to_embed = f"{summary}\n\n{content}"
        notes_data[note_id] = {
            "path": note_path,
            "post": post,
            "text": text_to_embed,
            "existing_links": post.get("links", [])
        }
        
        if note_id not in embeddings_db:
            print(f"Embedding new note: {note_id}")
            vector = embed_text(text_to_embed)
            embeddings_db[note_id] = vector
            new_embeddings_added = True
            
    if new_embeddings_added:
        save_embeddings(embeddings_db, EMBEDDINGS_FILE)
        
    # Phase 2: Compute similarities and link
    links_added = 0
    note_ids = list(notes_data.keys())
    
    for i, target_id in enumerate(note_ids):
        target_data = notes_data[target_id]
        target_vec = embeddings_db[target_id]
        
        new_links = []
        
        for candidate_id in note_ids:
            if candidate_id == target_id:
                continue
                
            # Check if already linked
            if candidate_id in target_data["existing_links"]:
                continue
                
            candidate_vec = embeddings_db[candidate_id]
            sim = cosine_similarity(target_vec, candidate_vec)
            
            if sim >= config.SIMILARITY_LINK_THRESHOLD:
                print(f"Match found! {target_id} <-> {candidate_id} (Score: {sim:.2f})")
                new_links.append(candidate_id)
                
        if new_links:
            # Update note
            post = target_data["post"]
            
            # Update frontmatter links
            existing = post.get("links", [])
            if not isinstance(existing, list):
                existing = []
            
            updated_links = list(set(existing + new_links))
            post["links"] = updated_links
            
            # Append wikilinks to body
            wikilink_text = "\n\n" + "\n".join([f"[[{link_id}]]" for link_id in new_links])
            post.content += wikilink_text
            
            # Save markdown
            with open(target_data["path"], "wb") as f:
                frontmatter.dump(post, f)
                
            target_data["existing_links"] = updated_links
            links_added += len(new_links)
            
    print(f"Auto-linking complete. Inserted {links_added} new links.")

if __name__ == "__main__":
    process_unlinked()
