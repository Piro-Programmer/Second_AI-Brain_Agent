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

# User State Management
_username = "default"

def set_user(username: str):
    global _username
    _username = username

def get_user() -> str:
    try:
        import streamlit as st
        # check if running inside Streamlit context
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        if get_script_run_ctx() is not None:
            if 'username' in st.session_state:
                return st.session_state['username']
    except Exception:
        pass
    return _username

# Dynamic Paths
def __getattr__(name):
    if name == "RAW_DIR":
        return f"users/{get_user()}/raw"
    if name == "WIKI_DIR":
        return f"users/{get_user()}/wiki"
    if name == "DATA_DIR":
        return f"users/{get_user()}/data"
    if name == "EMBEDDINGS_DIR":
        return f"users/{get_user()}/data/embeddings"
    if name == "GRAPH_PATH":
        return f"users/{get_user()}/data/graph.json"
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# LLM provider
LLM_PROVIDER = get_env_var("LLM_PROVIDER", "groq")
GROQ_API_KEY = get_env_var("GROQ_API_KEY")
XAI_API_KEY = get_env_var("XAI_API_KEY")
# Override via GROQ_MODEL in .env / Streamlit secrets when Groq retires a model
GROQ_MODEL = get_env_var("GROQ_MODEL", "openai/gpt-oss-20b")
GROQ_FALLBACK_MODEL = get_env_var("GROQ_FALLBACK_MODEL", "openai/gpt-oss-120b")
GROK_MODEL = "grok-2-1212"

# Embeddings & thresholds
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
SIMILARITY_LINK_THRESHOLD = 0.75
SIMILARITY_RETRIEVAL_MIN = 0.30

# PARA categories
PARA_CATEGORIES = ["Projects", "Areas", "Resources", "Archives"]
