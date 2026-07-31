import os
import json

def build_graph_html(graph_data: dict) -> str:
    """Reads static/graph.html, injects graph_data JSON, and returns HTML string."""
    template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "graph.html")
    
    with open(template_path, "r", encoding="utf-8") as f:
        html_template = f.read()
        
    # Inject the JSON string into the template
    graph_json = json.dumps(graph_data)
    html_content = html_template.replace("GRAPH_DATA_PLACEHOLDER", graph_json)
    
    return html_content
