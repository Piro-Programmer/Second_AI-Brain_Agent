import os
import glob
import json
import re
from datetime import datetime
import frontmatter
import lib.config as config
from lib.io import write_json

PARA_COLORS = {
    "Projects": "#FF6B6B",
    "Areas": "#4ECDC4",
    "Resources": "#45B7D1",
    "Archives": "#96CEB4"
}

def extract_wikilinks(body: str) -> list[str]:
    """Extract [[wikilinks]] from markdown body."""
    if not body:
        return []
    matches = re.findall(r"\[\[(.*?)\]\]", body)
    links = []
    seen = set()
    for m in matches:
        cleaned = m.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            links.append(cleaned)
    return links

def parse_wiki_note(path: str) -> dict:
    """Parse wiki frontmatter + body into a node dictionary."""
    try:
        post = frontmatter.load(path)
    except Exception as e:
        print(f"Warning: Failed to load frontmatter for {path}: {e}")
        return {}

    note_id = str(post.get("id", "")).strip()
    if not note_id:
        note_id = str(post.get("raw_id", "")).strip()
        if not note_id:
            note_id = os.path.splitext(os.path.basename(path))[0]

    summary = str(post.get("summary", "")).strip()
    if not summary:
        summary = os.path.splitext(os.path.basename(path))[0]

    para = str(post.get("para", "Resources")).strip()
    if not para:
        para = "Resources"

    tags = post.get("tags", [])
    if not isinstance(tags, list):
        tags = [str(tags)] if tags else []

    content = post.content or ""
    content_preview = content.strip()[:200]
    if len(content.strip()) > 200:
        content_preview += "..."

    color = PARA_COLORS.get(para, "#45B7D1")

    # Extract links from frontmatter and wikilinks from body
    frontmatter_links = post.get("links", [])
    if not isinstance(frontmatter_links, list):
        frontmatter_links = [str(frontmatter_links)] if frontmatter_links else []
    
    body_links = extract_wikilinks(content)
    
    all_links = []
    seen_links = set()
    for link in frontmatter_links + body_links:
        link_str = str(link).strip()
        if link_str and link_str != note_id and link_str not in seen_links:
            seen_links.add(link_str)
            all_links.append(link_str)

    return {
        "id": note_id,
        "label": summary if len(summary) <= 50 else summary[:47] + "...",
        "para": para,
        "tags": tags,
        "summary": summary,
        "content_preview": content_preview,
        "group": para,
        "color": color,
        "title": f"Summary: {summary}\n\nPreview: {content_preview}",
        "links": all_links
    }

def build_graph() -> dict:
    """Build in-memory nodes + edges from all wiki notes."""
    search_pattern = os.path.join(config.WIKI_DIR, "**", "*.md")
    note_paths = glob.glob(search_pattern, recursive=True)
    
    nodes = []
    note_links = {}
    valid_node_ids = set()
    
    # Parse all notes
    for path in sorted(note_paths):
        note_data = parse_wiki_note(path)
        if not note_data or not note_data.get("id"):
            continue
            
        note_id = note_data["id"]
        valid_node_ids.add(note_id)
        
        links = note_data.pop("links", [])
        note_links[note_id] = links
        
        nodes.append(note_data)
        
    # Build deduplicated edges
    edges_set = set()
    for source_id, links in note_links.items():
        for target_id in links:
            if source_id == target_id:
                continue
            if target_id not in valid_node_ids:
                continue
            u, v = min(source_id, target_id), max(source_id, target_id)
            edges_set.add((u, v))
            
    edges = [
        {
            "source": u,
            "target": v,
            "from": u,
            "to": v,
            "weight": 1.0,
            "type": "wikilink"
        }
        for u, v in sorted(edges_set)
    ]
    
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "node_count": len(nodes),
        "edge_count": len(edges)
    }
    
    return {
        "nodes": nodes,
        "edges": edges,
        "metadata": metadata
    }

def export_graph(output_path: str = config.GRAPH_PATH) -> str:
    """Export clean graph.json with nodes, edges, and metadata block."""
    graph_data = build_graph()
    write_json(graph_data, output_path)
    print(f"Graph exported to {output_path} ({graph_data['metadata']['node_count']} nodes, {graph_data['metadata']['edge_count']} edges)")
    return output_path

if __name__ == "__main__":
    export_graph()
