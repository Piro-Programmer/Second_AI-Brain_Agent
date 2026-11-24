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
# MiniLM scores clearly related short notes around 0.5-0.6, so 0.75 linked almost nothing
SIMILARITY_LINK_THRESHOLD = float(get_env_var("SIMILARITY_LINK_THRESHOLD", 0.50))
# Ask always sends the top-K notes to the LLM; this floor only drops clearly unrelated ones
SIMILARITY_RETRIEVAL_MIN = float(get_env_var("SIMILARITY_RETRIEVAL_MIN", 0.10))

# PARA categories
PARA_CATEGORIES = ["Projects", "Areas", "Resources", "Archives"]
