import os
import json
from typing import List, Any

def ensure_dir(path: str) -> None:
    """Ensure that a directory exists."""
    os.makedirs(path, exist_ok=True)

def read_text(path: str) -> str:
    """Read text from a file."""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_json(data: Any, path: str) -> None:
    """Write data to a JSON file."""
    ensure_dir(os.path.dirname(path))
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def list_files(directory: str, extension: str = None) -> List[str]:
    """List all files in a directory, optionally filtering by extension."""
    if not os.path.exists(directory):
        return []
    
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            if extension is None or filename.endswith(extension):
                files.append(os.path.join(root, filename))
    return files
