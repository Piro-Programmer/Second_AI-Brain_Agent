# SecondSelf — Your Personal AI Second Brain

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red.svg)](https://streamlit.io/)
[![Architecture](https://img.shields.io/badge/Architecture-Modular-success)](#architecture)

Every notes app fails the same way: information goes in, but knowledge never compounds. **SecondSelf** is a next-generation personal knowledge management system engineered to solve this. It is not just a notes app or a chatbot—it is a self-organizing brain that ingests unstructured data, autonomously links semantic relationships, visualizes your knowledge as a live graph, and acts as a Retrieval-Augmented Generation (RAG) oracle over your own thoughts.

### 🌟 For Recruiters & Senior Professionals
SecondSelf demonstrates end-to-end full-stack AI engineering. It showcases a robust understanding of modern LLM orchestration, local vector embeddings, and highly decoupled data pipelines. 

**Key Technical Highlights:**
- **Zero-Friction Ingestion Pipeline:** A robust CLI captures raw unstructured text, scrapes URLs (handling HTML sanitization via `BeautifulSoup`), and extracts text layers from PDFs (`pypdf`).
- **Autonomous Organization (PARA Method):** Leverages `Groq` or `xAI` models to classify raw inputs into actionable PARA categories (Projects, Areas, Resources, Archives) with auto-generated contextual tags and summaries.
- **Semantic Auto-Linking:** Computes local, high-dimensional embeddings via `sentence-transformers` to automatically discover and link semantically related notes, building a true knowledge graph without manual tagging.
- **Interactive Knowledge Visualization:** Parses frontmatter and markdown wikilinks to render a dynamic, force-directed graph of the user's brain topology.
- **Retrieval-Augmented Generation (RAG):** Answers natural language questions by retrieving contextually relevant notes and synthesizing them into highly accurate, sourced answers.
- **Stateless & Portable Architecture:** Employs a strictly file-based architecture (Markdown + YAML + JSON indices), eliminating database overhead and ensuring the user's data remains entirely portable, git-friendly, and infinitely extensible.

---

## 🚀 Quick Start Guide

### 1. Installation

Clone the repository and set up your virtual environment:

```bash
git clone https://github.com/Piro-Programmer/Second_AI-Brain.git
cd Second_AI-Brain

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

Open `.env` in your text editor and set your preferred LLM provider (`groq` or `grok`) along with the respective API key.

### 3. Running the Pipeline

**Step 1: Capture Knowledge**
Use the CLI to capture any note, link, or file. The pipeline automatically extracts the content, assigns a unique UUID and timestamp, and drops it into a highly structured `raw/` directory.

```bash
python capture.py --note "RAG systems use vector databases to augment LLM generation."
python capture.py --link "https://en.wikipedia.org/wiki/Knowledge_graph"
python capture.py --file "path/to/research_paper.pdf"
```

**Step 2: Launch the Brain UI**
Run the Streamlit dashboard to interact with your knowledge base and view your verification statistics.

```bash
streamlit run lib/app.py
```
*Open `http://localhost:8501` in your browser to view the dashboard!*

---

## 🏗️ Architecture Design

SecondSelf is built on a highly modular, decoupled, phase-wise pipeline:
1. **The Archivist:** `capture.py` -> Ingests anything to `raw/`.
2. **The Librarian:** `lib/classify.py` & `lib/link.py` -> AI organizes and connects data into `wiki/`.
3. **The Cartographer:** `lib/build_graph.py` -> Compiles a JSON topology of nodes and edges.
4. **The Oracle:** `lib/ask.py` & `lib/app.py` -> Streamlit UI for graph visualization and natural language Q&A.
