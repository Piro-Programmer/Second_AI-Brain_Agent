# SecondSelf — Your Personal AI Second Brain

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red.svg)](https://streamlit.io/)
[![Architecture](https://img.shields.io/badge/Architecture-Modular-success)](#architecture)

Every notes app fails the same way: information goes in, but knowledge never compounds. **SecondSelf** is a next-generation personal knowledge management system engineered to solve this. It is not just a notes app or a chatbot—it is a self-organizing brain that ingests unstructured data, autonomously links semantic relationships, visualizes your knowledge as a live graph, and acts as a Retrieval-Augmented Generation (RAG) oracle over your own thoughts.

### 🌟 For Recruiters & Senior Professionals
SecondSelf demonstrates end-to-end full-stack AI engineering. It showcases a robust understanding of modern LLM orchestration, local vector embeddings, and highly decoupled data pipelines. 

**Key Technical Highlights:**
- **Zero-Friction Ingestion Pipeline:** A robust CLI captures raw unstructured text, scrapes URLs (handling HTML sanitization via `BeautifulSoup`), and extracts text layers from PDFs (`pypdf`).
- **Autonomous Organization (PARA Method):** Leverages `Groq`-hosted models (with automatic fallback) to classify raw inputs into actionable PARA categories (Projects, Areas, Resources, Archives) with auto-generated contextual tags and summaries.
- **Semantic Auto-Linking:** Computes local, high-dimensional embeddings via `sentence-transformers` to automatically discover and link semantically related notes, building a true knowledge graph without manual tagging.
- **Interactive Knowledge Visualization:** Renders a dynamic, force-directed graph of each user's notes and the semantic links between them.
- **Retrieval-Augmented Generation (RAG):** Answers natural language questions by retrieving contextually relevant notes and synthesizing them into highly accurate, sourced answers.
- **Accounts & Persistent Storage:** Multi-user login with registration and email-based password reset. Users, notes and embeddings are stored in a database via SQLAlchemy: Supabase Postgres in the cloud, SQLite locally.

---

## 🚀 Quick Start Guide

### 1. Installation

Clone the repository and set up your virtual environment:

```bash
git clone https://github.com/Piro-Programmer/Second_AI-Brain_Agent.git
cd Second_AI-Brain_Agent

# Create and activate a virtual environment
python -m venv .venv

# On Windows:
.\.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy the example environment file and add your API keys:

```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

Open `.env` in your text editor and add your `GROQ_API_KEY`. Optionally set `GROQ_MODEL` / `GROQ_FALLBACK_MODEL` if Groq retires the default models.

| Setting | Needed for | Notes |
| --- | --- | --- |
| `DATABASE_URL` | Cloud deploys | Leave empty locally (uses `data/secondself.db`). On Streamlit Cloud use Supabase's **Session pooler** connection string. |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | Forgot password | e.g. Gmail with an App Password. Without these the reset tab says it isn't set up. |
| `AUTH_COOKIE_KEY` | Optional | Generated and stored in the database if empty. |

On Streamlit Cloud put the same keys in **App settings → Secrets** (TOML format).

### 3. Running the Pipeline

**Step 1: Capture Knowledge**
Capture from the app's sidebar, or from the CLI for a given user (`--user`, default `default`):

```bash
python capture.py --user alice --note "RAG systems use vector databases to augment LLM generation."
python capture.py --user alice --link "https://en.wikipedia.org/wiki/Knowledge_graph"
python capture.py --user alice --file "path/to/research_paper.pdf"
python brain_pipeline.py process --user alice
```

Upgrading from the old file storage (`users.yaml`, `users/<name>/`)? Import it once with `python scripts/migrate_files_to_db.py`.

**Step 2: Launch the Brain UI**
Run the Streamlit dashboard to interact with your knowledge base.

```bash
python -m streamlit run app.py
```
*Open `http://localhost:8501` in your browser to view the dashboard!*

---

## 🏗️ Architecture Design

SecondSelf is built on a highly modular, decoupled, phase-wise pipeline:
1. **The Archivist:** `capture.py` -> Saves anything as an unprocessed note in the database.
2. **The Librarian:** `lib/classify.py` & `lib/link.py` -> AI files each note into PARA, embeds it, and links related notes.
3. **The Cartographer:** `lib/build_graph.py` -> Builds the nodes-and-edges graph from the stored notes.
4. **The Oracle:** `ask.py` & `app.py` -> Streamlit UI for login, graph visualization and natural language Q&A.
5. **The Vault:** `lib/db.py` -> Users, notes, embeddings and reset codes (SQLAlchemy). `lib/password_reset.py` emails 6-digit reset codes.
