import hashlib
import numpy as np
from sentence_transformers import SentenceTransformer
import lib.config as config

_model = None

def get_model():
    global _model
    if _model is None:
        print(f"Loading embedding model ({config.EMBEDDING_MODEL})...")
        try:
            _model = SentenceTransformer(config.EMBEDDING_MODEL, local_files_only=True)
        except Exception:
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

    return float(np.dot(a, b) / (norm_a * norm_b))

def text_hash(text: str) -> str:
    """Fingerprint of the embedded text, so edited notes get re-embedded."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
