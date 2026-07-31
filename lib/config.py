import os
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()

def get_env_var(key, default=None):
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)

# Paths
RAW_DIR = "raw"
WIKI_DIR = "wiki"
DATA_DIR = "data"
EMBEDDINGS_DIR = "data/embeddings"
GRAPH_PATH = "data/graph.json"

# LLM provider
LLM_PROVIDER = get_env_var("LLM_PROVIDER", "groq")
GROQ_API_KEY = get_env_var("GROQ_API_KEY")
XAI_API_KEY = get_env_var("XAI_API_KEY")
GROQ_MODEL = "llama-3.1-8b-instant"
GROK_MODEL = "grok-2-1212"

# Embeddings & thresholds
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
SIMILARITY_LINK_THRESHOLD = 0.75
SIMILARITY_RETRIEVAL_MIN = 0.30

# PARA categories
PARA_CATEGORIES = ["Projects", "Areas", "Resources", "Archives"]
