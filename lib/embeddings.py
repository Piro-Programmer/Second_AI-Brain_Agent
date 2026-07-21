import os
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
import lib.config as config
from lib.io import ensure_dir

_model = None

def get_model():
    global _model
    if _model is None:
        print(f"Loading embedding model ({config.EMBEDDING_MODEL})...")
        _model = SentenceTransformer(config.EMBEDDING_MODEL)
    return _model

def embed_text(text: str) -> np.ndarray:
    model = get_model()
    return model.encode(text, convert_to_numpy=True)

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a = np.squeeze(a)
    b = np.squeeze(b)
    
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
        
    return np.dot(a, b) / (norm_a * norm_b)

def load_embeddings(filepath: str) -> dict:
    if os.path.exists(filepath):
        with open(filepath, "rb") as f:
            return pickle.load(f)
    return {}

def save_embeddings(embeddings: dict, filepath: str):
    ensure_dir(os.path.dirname(filepath))
    with open(filepath, "wb") as f:
        pickle.dump(embeddings, f)
