import re
from datetime import datetime
import lib.config as config
import lib.db as db

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

def note_to_node(note: dict) -> dict:
    """Shape a stored note into a vis-network node."""
    summary = note["summary"]
    content = note["content"].strip()
    content_preview = content[:200] + ("..." if len(content) > 200 else "")
    para = note["para"]
    return {
        "id": note["id"],
        "label": summary if len(summary) <= 50 else summary[:47] + "...",
        "para": para,
        "tags": note["tags"],
        "summary": summary,
        "content_preview": content_preview,
        "group": para,
        "color": PARA_COLORS.get(para, "#45B7D1"),
        "title": f"Summary: {summary}\n\nPreview: {content_preview}",
    }

def build_graph(username: str = None) -> dict:
    """Build nodes + deduplicated edges from a user's processed notes."""
    username = username or config.get_user()
    notes = db.get_notes(username, processed=True)
    nodes = [note_to_node(n) for n in notes]
    valid_ids = {n["id"] for n in notes}

    edges_set = set()
    for note in notes:
        for target_id in note["links"]:
            if target_id != note["id"] and target_id in valid_ids:
                edges_set.add((min(note["id"], target_id), max(note["id"], target_id)))

    edges = [
        {"source": u, "target": v, "from": u, "to": v, "weight": 1.0, "type": "semantic"}
        for u, v in sorted(edges_set)
    ]
    return {
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "node_count": len(nodes),
            "edge_count": len(edges),
        },
    }

def export_graph(username: str = None) -> dict:
    """Build the graph and print a summary (kept for the CLI pipeline)."""
    graph_data = build_graph(username)
    print(f"Graph built ({graph_data['metadata']['node_count']} nodes, "
          f"{graph_data['metadata']['edge_count']} edges)")
    return graph_data

if __name__ == "__main__":
    export_graph()
