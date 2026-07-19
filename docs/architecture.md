# SecondSelf — System Architecture

> **Project:** SecondSelf — Your Personal AI Second Brain
> **Purpose:** Define *how* we build the end-to-end system: capture → classify → link → graph → ask → deploy.

---

## 1. Executive Summary

SecondSelf is a **personal knowledge management system** that behaves like a self-organizing brain. Users capture unstructured information (notes, links, files); AI classifies and links it; the system renders an interactive knowledge graph; and a retrieval-augmented Q&A layer answers questions from the user's own accumulated knowledge.

The architecture is deliberately **modular and file-based** — each week adds a pipeline stage without rewriting prior work. Python scripts form the backend intelligence layer; JSON and Markdown files are the persistence layer; a Streamlit app is the unified UI; and free-tier cloud services handle LLM inference and deployment.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SecondSelf — High-Level View                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   [User Input]                                                              │
│       │ note / link / file / question                                       │
│       ▼                                                                     │
│   ┌──────────┐    ┌────────────┐    ┌──────────┐    ┌─────────────────┐  │
│   │ CAPTURE  │───▶│ CLASSIFY   │───▶│ AUTO-LINK│───▶│ GRAPH BUILDER   │  │
│   │ (Week 1) │    │ (Week 2.1) │    │ (Week 2.2)│    │ (Week 3)        │  │
│   └──────────┘    └────────────┘    └──────────┘    └────────┬────────┘  │
│        │                │                  │                     │          │
│        ▼                ▼                  ▼                     ▼          │
│     raw/             wiki/            embeddings/            graph.json     │
│                                                                             │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │                    STREAMLIT APP (Week 4)                            │  │
│   │  ┌─────────────────────┐      ┌──────────────────────────────────┐   │  │
│   │  │ Interactive Graph   │      │ Ask-Anything (RAG) Search Bar    │   │  │
│   │  │ (vis-network)       │      │ embeddings + wiki + LLM          │   │  │
│   │  └─────────────────────┘      └──────────────────────────────────┘   │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│                    [Public URL — Streamlit Cloud / HF Spaces]                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Design Principles

| Principle | Rationale |
|-----------|-----------|
| **File-first persistence** | No database setup; notes are portable, git-friendly, and debuggable. |
| **Pipeline stages are independent scripts** | Each week ships a working artifact; failures are isolated. |
| **Local-first, free-tier AI** | Embeddings run locally (`sentence-transformers`); LLM via Groq free tier. |
| **Idempotent processing** | Re-running classify/link/graph on the same input produces consistent output. |
| **Real data from day one** | Architecture assumes 10–15+ real captures, not synthetic fixtures. |
| **Single deployable surface** | Streamlit unifies graph + Q&A into one public URL. |

---

## 3. Technology Stack

### 3.1 Core Runtime

| Layer | Technology | Role |
|-------|------------|------|
| Language | Python 3.10+ | All pipeline scripts, Streamlit app |
| Package manager | `pip` + `requirements.txt` | Reproducible installs |
| UI framework | Streamlit | Graph embed + search bar + capture triggers |
| Graph rendering | vis-network (via `streamlit-agraph` or custom HTML component) | Force-directed interactive graph |
| Embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`) | Local, free semantic similarity |
| LLM | Groq API + Llama 3 | Classification, summarization, answer synthesis |
| Deployment | Streamlit Community Cloud or Hugging Face Spaces | Free public URL |

### 3.2 Key Python Dependencies

```
streamlit
groq                          # or openai-compatible client for Groq
sentence-transformers
numpy
python-frontmatter          # optional: YAML frontmatter in wiki notes
requests                      # URL fetching for link captures
beautifulsoup4                # HTML extraction from captured links
pypdf / pdfplumber            # PDF text extraction
python-dotenv                 # API key management
```

### 3.3 External Services

| Service | Usage | Cost |
|---------|-------|------|
| Groq API | PARA classification, tag generation, RAG answer synthesis | Free tier |
| Streamlit Cloud | Hosting `app.py` | Free tier |
| GitHub | Source repo + CI optional | Free |

---

## 4. Repository Structure

```
secondself/
├── raw/                          # Immutable capture store (append-only)
│   └── {timestamp}_{uuid}.{ext}  # e.g. 20250717_143022_a1b2c3d4.txt
│
├── wiki/                         # Processed, classified, linked notes
│   └── {para_category}/
│       └── {note_id}.md          # Markdown with frontmatter + wikilinks
│
├── data/                         # Derived indices (not hand-edited)
│   ├── embeddings/
│   │   └── {note_id}.npy         # Per-note embedding vectors
│   ├── embeddings_index.json     # note_id → file path + metadata
│   └── graph.json                # Nodes + edges for visualization
│
├── static/                       # Frontend assets for graph
│   └── graph_template.html       # vis-network template (if not using agraph)
│
├── capture.py                    # Week 1: CLI capture entry point
├── classify.py                   # Week 2.1: PARA + tags + summary
├── link.py                       # Week 2.2: Embeddings + auto-linking
├── build_graph.py                # Week 3.1: wiki → graph.json
├── ask.py                        # Week 4.1: RAG Q&A function
├── app.py                        # Week 4.2: Streamlit unified UI
├── pipeline.py                   # Optional: orchestrate full pipeline
├── config.py                     # Shared constants, paths, thresholds
├── utils/
│   ├── io.py                     # File read/write helpers
│   ├── llm.py                    # Groq client wrapper
│   ├── embeddings.py             # Load model, encode, similarity
│   └── parsers.py                # Note/link/file content extraction
│
├── .env.example                  # GROQ_API_KEY placeholder
├── .gitignore                    # raw/, .env, __pycache__, .npy
├── requirements.txt
├── README.md
├── architecture.md
├── implementation-plan.md
└── edge-case.md
```

> **Note:** `raw/` may be gitignored if captures are personal; `wiki/` and `data/graph.json` can be committed as demo artifacts.

---

## 5. Data Models

### 5.1 Raw Capture Record

Every item in `raw/` follows a consistent naming and metadata convention.

**Filename pattern:**
```
{YYYYMMDD_HHMMSS}_{short_uuid}.{ext}
```

**Sidecar metadata (optional JSON alongside file):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "timestamp": "2025-07-17T14:30:22+05:30",
  "source_type": "note | link | file",
  "original_filename": "research-ideas.pdf",
  "content_hash": "sha256:..."
}
```

**Capture types:**

| Type | Input | Stored as |
|------|-------|-----------|
| Note | CLI string or stdin | `.txt` or `.md` |
| Link | URL | `.md` with fetched title + excerpt + URL |
| File | Path to PDF/image/doc | Original extension; text extracted to sidecar `.txt` if needed |

### 5.2 Wiki Note (Processed)

Wiki notes use **Markdown + YAML frontmatter** for machine-readability and human readability.

```markdown
---
id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
raw_source: raw/20250717_143022_a1b2c3d4.txt
para_category: Projects
tags: [python, side-project, ai]
summary: "A one-line summary generated by LLM"
created_at: 2025-07-17T14:30:22+05:30
processed_at: 2025-07-17T15:00:00+05:30
links: [b2c3d4e5-note-id, c3d4e5f6-note-id]
---

# Note Title (optional, from summary or first line)

Full note body content here.

## Related
- [[b2c3d4e5-note-id]]
- [[c3d4e5f6-note-id]]
```

**PARA categories (exactly one per note):**

| Category | Meaning | Example content |
|----------|---------|-----------------|
| **Projects** | Active, outcome-bound work | "Build SecondSelf by Week 4" |
| **Areas** | Ongoing responsibilities | "Health", "Finances" |
| **Resources** | Reference material for future use | Articles, tutorials, bookmarks |
| **Archives** | Inactive/completed items | Old project notes |

### 5.3 Embedding Index Entry

```json
{
  "note_id": "a1b2c3d4",
  "wiki_path": "wiki/Projects/a1b2c3d4.md",
  "para_category": "Projects",
  "embedding_file": "data/embeddings/a1b2c3d4.npy",
  "dimensions": 384,
  "text_used": "summary + first 500 chars of body"
}
```

### 5.4 Graph Schema (`graph.json`)

```json
{
  "metadata": {
    "generated_at": "2025-07-17T16:00:00+05:30",
    "node_count": 15,
    "edge_count": 23
  },
  "nodes": [
    {
      "id": "a1b2c3d4",
      "label": "Build SecondSelf pipeline",
      "para_category": "Projects",
      "tags": ["python", "ai"],
      "summary": "One-line summary",
      "wiki_path": "wiki/Projects/a1b2c3d4.md",
      "content_preview": "First 200 chars for hover popup"
    }
  ],
  "edges": [
    {
      "source": "a1b2c3d4",
      "target": "b2c3d4e5",
      "similarity": 0.82,
      "type": "semantic_link"
    }
  ]
}
```

---

## 6. Component Architecture

### 6.1 Capture Module (`capture.py`) — Week 1

**Responsibility:** Accept any input type and persist immutably to `raw/`.

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│ CLI Args    │────▶│ Content Detector │────▶│ Raw Writer  │
│ --note      │     │ note/link/file   │     │ + metadata  │
│ --link      │     └──────────────────┘     └─────────────┘
│ --file      │
└─────────────┘
```

**Public interface:**

```python
def capture_note(text: str) -> str: ...       # returns raw file path
def capture_link(url: str) -> str: ...
def capture_file(file_path: str) -> str: ...
def generate_capture_id() -> str: ...
```

**Behavior:**
- Generate UUID + ISO timestamp on every capture.
- For links: fetch page, extract title and main text (fallback: URL only).
- For files: copy to `raw/` with hashed name; extract text if PDF.
- Never overwrite existing captures (append-only).

---

### 6.2 Classification Module (`classify.py`) — Week 2.1

**Responsibility:** Transform raw captures into organized wiki notes with PARA category, tags, and summary.

```
┌──────────┐     ┌─────────────┐     ┌────────────────┐     ┌──────────┐
│ raw/     │────▶│ Unprocessed │────▶│ Groq LLM       │────▶│ wiki/    │
│ files    │     │ filter      │     │ PARA+tags+sum  │     │ *.md     │
└──────────┘     └─────────────┘     └────────────────┘     └──────────┘
```

**Public interface:**

```python
def classify_raw(raw_path: str) -> dict:
    """Returns {category, tags, summary, title}"""

def process_unclassified() -> list[str]:
    """Batch: all raw files without a wiki counterpart. Returns wiki paths."""

def build_classification_prompt(content: str) -> str: ...
```

**LLM prompt structure (classification):**

```
You are a personal knowledge organizer using the PARA method.
Given the following capture, respond in JSON only:
{
  "para_category": "Projects|Areas|Resources|Archives",
  "tags": ["tag1", "tag2"],
  "summary": "one line",
  "title": "short title"
}

Capture:
---
{content}
---
```

**Processing rules:**
- Skip raw files that already have a corresponding wiki note (match by `raw_source` in frontmatter).
- Write wiki file to `wiki/{para_category}/{id}.md`.
- Log failures to `data/classify_errors.log` without halting batch.

---

### 6.3 Auto-Link Module (`link.py`) — Week 2.2

**Responsibility:** Compute embeddings and insert wikilinks between semantically related notes.

```
┌────────────┐     ┌───────────────────┐     ┌─────────────────┐
│ wiki/ note │────▶│ sentence-         │────▶│ Similarity scan │
│ (new)      │     │ transformers enc  │     │ vs all existing │
└────────────┘     └───────────────────┘     └────────┬────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │ If sim ≥ 0.75   │
                                              │ insert [[link]] │
                                              │ update frontmatter│
                                              └─────────────────┘
```

**Public interface:**

```python
def embed_note(wiki_path: str) -> np.ndarray: ...
def find_similar(note_id: str, top_k: int = 5) -> list[tuple[str, float]]: ...
def auto_link_note(wiki_path: str, threshold: float = 0.75) -> list[str]: ...
def process_all_unlinked() -> int: ...   # returns count of links created
```

**Similarity strategy:**
- Encode: `summary + "\n" + body[:500]` for each note.
- Compare new note against all existing embeddings (brute force OK for <500 notes).
- Threshold default: **0.75** (tunable in `config.py`).
- Bidirectional links: if A links to B, also add B → A (optional but recommended).

**Persistence:**
- Save `.npy` per note in `data/embeddings/`.
- Maintain `data/embeddings_index.json` for fast lookup.

---

### 6.4 Graph Builder (`build_graph.py`) — Week 3.1

**Responsibility:** Parse wiki notes and links into a nodes-and-edges JSON graph.

```
┌──────────┐     ┌─────────────────┐     ┌─────────────┐
│ wiki/    │────▶│ Parse frontmatter│────▶│ graph.json  │
│ *.md     │     │ + [[wikilinks]]  │     │ nodes+edges │
└──────────┘     └─────────────────┘     └─────────────┘
```

**Public interface:**

```python
def parse_wiki_note(path: str) -> dict: ...
def extract_wikilinks(body: str) -> list[str]: ...
def build_graph() -> dict: ...
def export_graph(output_path: str = "data/graph.json") -> str: ...
```

**Edge sources (two types):**
1. **Explicit wikilinks** — `[[note_id]]` in markdown body (from auto-link step).
2. **Semantic edges** — from `links` array in frontmatter with stored similarity score.

**Node visual attributes (for frontend):**

| PARA Category | Color |
|---------------|-------|
| Projects | `#FF6B6B` |
| Areas | `#4ECDC4` |
| Resources | `#45B7D1` |
| Archives | `#96CEB4` |

---

### 6.5 RAG Q&A Module (`ask.py`) — Week 4.1

**Responsibility:** Answer natural-language questions using retrieved wiki notes + LLM synthesis.

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│ User question│────▶│ Embed question  │────▶│ Top-K retrieve│
└──────────────┘     └─────────────────┘     └──────┬───────┘
                                                      │
                                                      ▼
┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│ Answer text  │◀────│ Groq LLM        │◀────│ Build context │
│ + sources    │     │ synthesis       │     │ from wiki/    │
└──────────────┘     └─────────────────┘     └──────────────┘
```

**Public interface:**

```python
def ask(question: str, top_k: int = 5) -> dict:
    """
    Returns:
    {
      "answer": "synthesized answer",
      "sources": [{"note_id", "summary", "wiki_path", "score"}],
      "confidence": "high|medium|low"
    }
    """
```

**RAG prompt structure:**

```
You are a personal knowledge assistant. Answer ONLY from the provided notes.
If the notes don't contain enough information, say so honestly.
Cite which notes you used.

Notes:
{retrieved_note_1}
---
{retrieved_note_2}
---

Question: {question}
```

**Retrieval parameters:**
- `top_k = 5` notes by cosine similarity.
- Minimum similarity floor: `0.3` (below this → "I don't have notes on that").
- Include source note IDs in response for transparency.

---

### 6.6 Streamlit App (`app.py`) — Week 4.2

**Responsibility:** Unified UI combining graph visualization, Q&A, and optional capture.

```
┌────────────────────────────────────────────────────────────┐
│  SecondSelf — Your Personal AI Second Brain                │
├────────────────────────────────────────────────────────────┤
│  [Sidebar]                                                  │
│    • Run Pipeline (classify → link → graph)                │
│    • Capture new note / link                               │
│    • Stats: N notes, N links                               │
├────────────────────────────────────────────────────────────┤
│  [Tab 1: Brain Graph]                                       │
│    Interactive force-directed graph (vis-network)          │
│    Hover → note summary + preview                          │
│    Click → full note in expander                           │
├────────────────────────────────────────────────────────────┤
│  [Tab 2: Ask Anything]                                      │
│    Text input + Ask button                                 │
│    Answer + source citations                               │
└────────────────────────────────────────────────────────────┘
```

**Key Streamlit components:**
- `st.tabs()` — Graph | Ask
- `streamlit-agraph` or `components.html()` — embed vis-network
- `st.text_input()` + `st.button("Ask")` — Q&A interface
- `st.sidebar` — pipeline controls and capture form

**Graph rendering approach (recommended):**

| Option | Pros | Cons |
|--------|------|------|
| `streamlit-agraph` | Native Streamlit integration | Less customization |
| Custom HTML + vis-network | Full hover/drag/zoom control | More setup |

**Recommendation:** Start with `streamlit-agraph`; migrate to custom vis-network HTML if hover popups need richer content.

---

## 7. End-to-End Data Flow

```
1. CAPTURE
   User: python capture.py --note "idea about RAG"
   → raw/20250717_120000_abc123.txt

2. CLASSIFY
   User: python classify.py
   → Groq returns {Projects, [rag, ai], "RAG architecture idea"}
   → wiki/Projects/abc123.md

3. AUTO-LINK
   User: python link.py
   → Embedding computed for abc123
   → Similar to def456 (score 0.81)
   → Both notes updated with [[wikilinks]]

4. BUILD GRAPH
   User: python build_graph.py
   → data/graph.json (nodes: 15, edges: 23)

5. ASK
   User: python ask.py "What do I know about RAG?"
   → Retrieves Projects/abc123 + Resources/def456
   → LLM synthesizes answer with citations

6. UI (deployed)
   User opens public URL
   → Streamlit loads graph.json + serves ask() interactively
```

**Orchestration script (`pipeline.py`):**

```python
def run_full_pipeline():
    process_unclassified()   # classify
    process_all_unlinked()   # link
    export_graph()           # graph
```

---

## 8. Configuration (`config.py`)

Centralized constants to avoid magic numbers:

```python
# Paths
RAW_DIR = "raw"
WIKI_DIR = "wiki"
DATA_DIR = "data"
GRAPH_PATH = "data/graph.json"
EMBEDDINGS_DIR = "data/embeddings"
EMBEDDINGS_INDEX = "data/embeddings_index.json"

# Models
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
LLM_MODEL = "llama3-8b-8192"          # Groq model ID
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Thresholds
SIMILARITY_LINK_THRESHOLD = 0.75       # auto-link
SIMILARITY_RETRIEVAL_MIN = 0.30        # RAG minimum relevance
RAG_TOP_K = 5

# PARA
PARA_CATEGORIES = ["Projects", "Areas", "Resources", "Archives"]
```

---

## 9. Security & Secrets

| Concern | Mitigation |
|---------|------------|
| API keys in repo | `.env` file + `.gitignore`; use Streamlit Cloud secrets |
| Personal data in `raw/` | Gitignore `raw/` by default; document in README |
| Prompt injection via captures | Sanitize content before LLM; use system prompt boundaries |
| URL fetching (SSRF) | Validate URLs; block private IP ranges; timeout fetches |
| Deployed app access | Public read-only demo; no write access to raw/ in production |

**Streamlit Cloud secrets format:**
```toml
GROQ_API_KEY = "gsk_..."
```

---

## 10. Deployment Architecture

```
┌──────────────┐         ┌─────────────────────┐         ┌─────────────┐
│ GitHub Repo  │────────▶│ Streamlit Cloud     │────────▶│ Public URL  │
│ (app.py)     │  push   │ • pip install       │  HTTPS  │ *.streamlit │
│ wiki/ demo   │         │ • streamlit run     │         │   .app      │
│ graph.json   │         │ • secrets: GROQ_KEY │         └─────────────┘
└──────────────┘         └─────────────────────┘
```

**Deployment checklist:**
1. Commit `app.py`, `requirements.txt`, demo `wiki/` + `data/graph.json`.
2. Connect repo to Streamlit Cloud.
3. Set `GROQ_API_KEY` in app secrets.
4. Main file: `app.py`.
5. Verify graph renders and ask() returns answers on live URL.

**Alternative:** Hugging Face Spaces with `sdk: streamlit` in README frontmatter.

---

## 11. Week-to-Architecture Mapping

| Week | Badge | Modules | Persistent Artifacts | Acceptance Gate |
|------|-------|---------|---------------------|-----------------|
| 1 | The Archivist | `capture.py`, `utils/parsers.py` | `raw/` (10+ items) | Timestamp + UUID on every capture |
| 2 | The Librarian | `classify.py`, `link.py`, `utils/llm.py`, `utils/embeddings.py` | `wiki/`, `data/embeddings/` | PARA + auto-links on 15+ items |
| 3 | The Cartographer | `build_graph.py`, graph frontend | `data/graph.json` | Interactive graph with hover/drag/zoom |
| 4 | The Oracle | `ask.py`, `app.py`, deployment | Live public URL | Full pipeline + RAG in one app |

---

## 12. Module Dependency Graph

```
capture.py
    └── utils/parsers.py, utils/io.py

classify.py
    └── utils/llm.py, utils/io.py, config.py

link.py
    └── utils/embeddings.py, utils/io.py, config.py

build_graph.py
    └── utils/io.py, config.py

ask.py
    └── utils/embeddings.py, utils/llm.py, utils/io.py, config.py

app.py
    └── ask.py, build_graph.py (or reads graph.json directly)
    └── pipeline.py (optional sidebar trigger)
```

**Dependency rule:** Lower-level modules (`utils/`, `config.py`) must not import from pipeline scripts.

---

## 13. Performance Expectations

For personal-scale usage (10–500 notes):

| Operation | Expected latency |
|-----------|------------------|
| Single capture | < 1s |
| Classify one note (Groq API) | 1–3s |
| Embed one note (local CPU) | 0.5–2s |
| Auto-link scan (100 notes) | 2–10s |
| Build graph.json | < 1s |
| ask() (retrieve + LLM) | 3–8s |
| Graph render (100 nodes) | 1–3s in browser |

No caching layer or database is required at this scale. If notes exceed ~1,000, consider `faiss` for approximate nearest-neighbor search.

---

## 14. Testing Strategy

| Level | What to test | How |
|-------|--------------|-----|
| Unit | Parsers, wikilink extraction, ID generation | pytest on sample strings |
| Integration | classify → wiki file created | Run on one raw file, assert frontmatter |
| Integration | link → wikilinks inserted | Two similar notes, assert mutual links |
| E2E | Full pipeline | capture 3 items → pipeline → graph.json has 3 nodes |
| Manual | Graph UI | Hover, drag, zoom in browser |
| Manual | ask() | Ask question answerable from your real notes |

**Test with real data** — the problem statement explicitly requires real captures, not fixtures.

---

## 15. Future Extensions (Out of Scope for MVP)

- Vector DB (Chroma, FAISS) for large corpora
- Multi-user auth and per-user knowledge bases
- Scheduled background ingestion (browser extension, email forwarding)
- Incremental graph updates via WebSocket
- Voice capture and transcription
- Mobile-friendly PWA wrapper

---

## 16. Architecture Decision Records (ADRs)

### ADR-001: File-based storage over database
**Decision:** Use `raw/`, `wiki/`, and JSON indices.
**Reason:** Zero infra setup, git-portable, matches 4-week scope.
**Trade-off:** No concurrent write safety; acceptable for single-user CLI.

### ADR-002: Local embeddings, cloud LLM
**Decision:** `sentence-transformers` locally; Groq for generation.
**Reason:** Free, fast enough, no embedding API costs.
**Trade-off:** First run downloads ~80MB model.

### ADR-003: Markdown + frontmatter for wiki
**Decision:** YAML frontmatter + `[[wikilinks]]`.
**Reason:** Human-readable, machine-parseable, Obsidian-compatible.
**Trade-off:** Manual edit can break frontmatter schema.

### ADR-004: Streamlit as unified UI
**Decision:** Single `app.py` for graph + Q&A + deploy.
**Reason:** Fastest path to public URL with Python-only stack.
**Trade-off:** Limited UI customization vs React SPA.

### ADR-005: Brute-force similarity search
**Decision:** NumPy cosine similarity over all embeddings.
**Reason:** <500 notes = sub-second search on CPU.
**Trade-off:** Replace with FAISS if corpus grows.

---

## 17. Glossary

| Term | Definition |
|------|------------|
| **PARA** | Projects, Areas, Resources, Archives — Tiago Forte's organization framework |
| **RAG** | Retrieval-Augmented Generation — retrieve relevant docs, then LLM synthesizes answer |
| **Wikilink** | `[[note_id]]` syntax linking one note to another |
| **Embedding** | Dense vector representation of text for semantic similarity |
| **Force-directed graph** | Layout algorithm where connected nodes pull together, unconnected repel |

---

*This document is the canonical architecture reference. Implementation details and phase ordering live in `implementation-plan.md`. Corner cases live in `edge-case.md`.*
