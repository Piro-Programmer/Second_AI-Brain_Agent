# SecondSelf — Phase-Wise Implementation Plan

> **References:** [`architecture.md`](architecture.md) · [`PROBLEM_STATEMENT.md`](PROBLEM_STATEMENT.md)
> **Goal:** Build capture → classify → link → graph → ask → deploy, one phase at a time.

---

## Overview

This plan breaks the 4-week SecondSelf project into **10 phases**. Phases 0–5 implement code; Phases 6–7 validate locally; Phases 8–9 ship to production.

```
Phase 0   Setup & scaffolding
Phase 1   Capture pipeline          ── Week 1  🏅 The Archivist
Phase 2   Auto-classify (PARA)      ── Week 2.1
Phase 3   Auto-link (embeddings)    ── Week 2.2 🏅 The Librarian
Phase 4   Graph builder + viz       ── Week 3   🏅 The Cartographer
Phase 5   RAG + Streamlit app       ── Week 4   🏅 The Oracle
Phase 6   Local module testing
Phase 7   Local end-to-end testing
Phase 8   Deploy to public URL
Phase 9   Final production testing
```

### Phase Dependency Graph

```
Phase 0
   │
   ▼
Phase 1 (capture)
   │
   ▼
Phase 2 (classify) ──▶ Phase 3 (link)
                           │
                           ▼
                      Phase 4 (graph)
                           │
                           ▼
                      Phase 5 (ask + app)
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
         Phase 6                   Phase 7
         (unit/integration)        (E2E local)
              │                         │
              └────────────┬────────────┘
                           ▼
                      Phase 8 (deploy)
                           │
                           ▼
                      Phase 9 (prod test)
```

---

## Phase 0 — Project Setup

**Goal:** Scaffold the repo, install dependencies, configure secrets, and create shared utilities so every later phase starts from a clean foundation.

**Maps to:** Pre-Week 1 · Architecture §4, §8

### Tasks

| #    | Task                       | Output                                                                                                   |
| ---- | -------------------------- | -------------------------------------------------------------------------------------------------------- |
| 0.1  | Create directory structure | `raw/`, `wiki/`, `data/embeddings/`, `static/`, `utils/`                                                 |
| 0.2  | Create `config.py`         | Paths, model names, thresholds, PARA categories, `LLM_PROVIDER`                                          |
| 0.3  | Create `utils/io.py`       | `ensure_dir()`, `read_text()`, `write_json()`, `list_files()`                                            |
| 0.4  | Create `utils/__init__.py` | Package init                                                                                             |
| 0.5  | Create `requirements.txt`  | All dependencies pinned loosely (incl. `groq` + `openai` for Grok)                                       |
| 0.6  | Create `.env.example`      | `LLM_PROVIDER`, `GROQ_API_KEY`, `XAI_API_KEY` placeholders                                               |
| 0.7  | Create `.gitignore`        | `.env`, `__pycache__/`, `*.pyc`, optional `raw/`                                                         |
| 0.8  | Create virtual environment | `python -m venv .venv`                                                                                   |
| 0.9  | Install dependencies       | `pip install -r requirements.txt`                                                                        |
| 0.10 | Register LLM API keys      | Copy `.env.example` → `.env`; set `LLM_PROVIDER` + matching key                                          |
| 0.11 | Create placeholder scripts | Empty stubs: `capture.py`, `classify.py`, `link.py`, `build_graph.py`, `ask.py`, `app.py`, `pipeline.py` |
| 0.12 | Add `.gitkeep` files       | Keep empty dirs in git: `raw/`, `wiki/`, `data/embeddings/`                                              |

### Files to Create

```
secondself/
├── raw/.gitkeep
├── wiki/.gitkeep
├── data/
│   └── embeddings/.gitkeep
├── static/
├── utils/
│   ├── __init__.py
│   └── io.py
├── config.py
├── capture.py          # stub
├── classify.py         # stub
├── link.py             # stub
├── build_graph.py      # stub
├── ask.py              # stub
├── app.py              # stub
├── pipeline.py         # stub
├── requirements.txt
├── .env.example
└── .gitignore
```

### `requirements.txt` (initial)

```
streamlit>=1.32.0
groq>=0.9.0
openai>=1.30.0                # xAI Grok (OpenAI-compatible API)
sentence-transformers>=2.7.0
numpy>=1.26.0
python-frontmatter>=1.1.0
requests>=2.31.0
beautifulsoup4>=4.12.0
pypdf>=4.0.0
python-dotenv>=1.0.0
streamlit-agraph>=0.0.45
```

### `.env.example`

```env
# LLM provider: "groq" (default) or "grok"
LLM_PROVIDER=groq

# Groq — https://console.groq.com
GROQ_API_KEY=your_groq_key_here

# xAI Grok — https://console.x.ai
XAI_API_KEY=your_xai_grok_key_here
```

### `config.py` — Key Variables

```python
# Paths
RAW_DIR, WIKI_DIR, DATA_DIR, EMBEDDINGS_DIR, GRAPH_PATH

# LLM provider (Architecture §6.0)
LLM_PROVIDER          # "groq" (default) | "grok"
GROQ_API_KEY          # required when LLM_PROVIDER=groq
XAI_API_KEY           # required when LLM_PROVIDER=grok
GROQ_MODEL            # default: "llama-3.1-8b-instant"
GROK_MODEL            # default: "grok-2-1212"

# Embeddings & thresholds
EMBEDDING_MODEL       # default: "all-MiniLM-L6-v2"
SIMILARITY_LINK_THRESHOLD   # default: 0.75
SIMILARITY_RETRIEVAL_MIN    # default: 0.30

# PARA categories
PARA_CATEGORIES = ["Projects", "Areas", "Resources", "Archives"]
```

### LLM Provider Reference

| Provider | Env var        | Default model          | SDK      | Base URL              |
| -------- | -------------- | ---------------------- | -------- | --------------------- |
| `groq`   | `GROQ_API_KEY` | `llama-3.1-8b-instant` | `groq`   | Groq API              |
| `grok`   | `XAI_API_KEY`  | `grok-2-1212`          | `openai` | `https://api.x.ai/v1` |

`classify.py` and `ask.py` never import provider SDKs directly — they call `utils/llm.py`.

### Commands

```bash
cd secondself
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
```

### Acceptance Criteria

- [ ] All directories exist per architecture §4
- [ ] `pip install -r requirements.txt` succeeds without errors
- [ ] `config.py` imports cleanly: `python -c "import config"`
- [ ] `.env` contains valid API key for chosen provider (`GROQ_API_KEY` or `XAI_API_KEY`)
- [ ] `LLM_PROVIDER` set to `groq` or `grok` in `.env`
- [ ] Git repo initialized; sensitive files excluded

### Estimated Effort

**2–3 hours**

---

## Phase 1 — Capture Pipeline (Week 1)

**Goal:** One command captures any note, link, or file into `raw/` with timestamp + unique ID.

**Badge:** 🏅 The Archivist

**Maps to:** Problem Statement Week 1 · Architecture §6.1

### Tasks

| #   | Task                                                        | File                             |
| --- | ----------------------------------------------------------- | -------------------------------- |
| 1.1 | Implement ID + timestamp generation                         | `capture.py`                     |
| 1.2 | Implement note capture (CLI string / stdin)                 | `capture.py`                     |
| 1.3 | Implement link capture (fetch URL, extract title + text)    | `capture.py`, `utils/parsers.py` |
| 1.4 | Implement file capture (copy + PDF text extraction)         | `capture.py`, `utils/parsers.py` |
| 1.5 | Write sidecar metadata JSON per capture                     | `capture.py`                     |
| 1.6 | Add CLI entry point with `--note`, `--link`, `--file` flags | `capture.py`                     |
| 1.7 | Capture 10+ real items from your own scattered info         | manual                           |

### Key Functions

```python
# capture.py
def generate_capture_id() -> str: ...
def capture_note(text: str) -> str: ...
def capture_link(url: str) -> str: ...
def capture_file(file_path: str) -> str: ...
```

```python
# utils/parsers.py
def fetch_link_content(url: str) -> dict: ...   # {title, text, url}
def extract_pdf_text(file_path: str) -> str: ...
def detect_source_type(input_value: str) -> str: ...
```

### Filename Convention

```
raw/{YYYYMMDD_HHMMSS}_{short_uuid}.{ext}
raw/{YYYYMMDD_HHMMSS}_{short_uuid}.meta.json
```

### Commands to Test

```bash
python capture.py --note "Idea: use RAG for personal notes"
python capture.py --link "https://python.org"
python capture.py --file "path/to/document.pdf"
```

### Acceptance Criteria

- [ ] `raw/` and `wiki/` folder structure exists
- [ ] One command captures a note, a link, AND a file
- [ ] Every capture has a timestamp + unique ID (in filename and metadata)
- [ ] Captures are append-only (no overwrites)
- [ ] **10+ real items** in `raw/` (not test data)

### Estimated Effort

**4–6 hours**

---

## Phase 2 — Auto-Classify with PARA (Week 2.1)

**Goal:** Send raw captures to an LLM (Groq/Llama 3 or Grok/xAI) and produce organized wiki notes with PARA category, tags, and summary.

**Maps to:** Problem Statement Week 2.1 · Architecture §6.2

**Depends on:** Phase 1 (raw captures exist)

### Tasks

| #   | Task                                               | File           |
| --- | -------------------------------------------------- | -------------- |
| 2.1 | Create multi-provider LLM wrapper (Groq + Grok)    | `utils/llm.py` |
| 2.2 | Build classification prompt (JSON response)        | `classify.py`  |
| 2.3 | Implement `classify_raw(raw_path)`                 | `classify.py`  |
| 2.4 | Write wiki Markdown with YAML frontmatter          | `classify.py`  |
| 2.5 | Create PARA subdirectories under `wiki/`           | `classify.py`  |
| 2.6 | Implement batch processor `process_unclassified()` | `classify.py`  |
| 2.7 | Skip already-processed raw files (idempotent)      | `classify.py`  |
| 2.8 | Log failures to `data/classify_errors.log`         | `classify.py`  |
| 2.9 | Run on all Phase 1 captures                        | manual         |

### Key Functions

```python
# utils/llm.py — provider-agnostic; routes to Groq or Grok based on LLM_PROVIDER
def get_llm_provider() -> str: ...          # "groq" | "grok"
def call_llm(prompt: str, system: str = "") -> str: ...
def call_llm_json(prompt: str) -> dict: ...

# classify.py
def build_classification_prompt(content: str) -> str: ...
def classify_raw(raw_path: str) -> dict: ...
def write_wiki_note(raw_path: str, classification: dict) -> str: ...
def process_unclassified() -> list[str]: ...
```

### Wiki Output Path

```
wiki/{para_category}/{note_id}.md
```

Example: `wiki/Projects/a1b2c3d4.md`

### Commands to Test

```bash
python classify.py                    # batch: all unclassified
python classify.py --file raw/20250717_120000_abc123.txt   # single file

# Verify provider routing (after utils/llm.py exists)
python -c "from utils.llm import get_llm_provider; print(get_llm_provider())"
```

### Acceptance Criteria

- [ ] Any raw capture → category + tags + summary automatically
- [ ] PARA categorization working (Projects, Areas, Resources, Archives)
- [ ] Wiki notes have valid YAML frontmatter
- [ ] Re-running classify skips already-processed files
- [ ] Failures logged without stopping the batch
- [ ] Works with both `LLM_PROVIDER=groq` and `LLM_PROVIDER=grok`

### Estimated Effort

**5–7 hours**

---

## Phase 3 — Auto-Link with Embeddings (Week 2.2)

**Goal:** Compute local embeddings, find semantically related notes, and auto-insert wikilinks.

**Badge:** 🏅 The Librarian (complete Week 2)

**Maps to:** Problem Statement Week 2.2 · Architecture §6.3

**Depends on:** Phase 2 (wiki notes exist)

### Tasks

| #    | Task                                                                      | File                  |
| ---- | ------------------------------------------------------------------------- | --------------------- |
| 3.1  | Load `sentence-transformers` model (lazy singleton)                       | `utils/embeddings.py` |
| 3.2  | Implement `embed_text(text)` and `embed_note(wiki_path)`                  | `utils/embeddings.py` |
| 3.3  | Save embeddings as `.npy` per note                                        | `link.py`             |
| 3.4  | Maintain `data/embeddings_index.json`                                     | `link.py`             |
| 3.5  | Implement cosine similarity search                                        | `utils/embeddings.py` |
| 3.6  | Implement `find_similar(note_id, top_k)`                                  | `link.py`             |
| 3.7  | Auto-insert `[[wikilinks]]` when similarity ≥ 0.75                        | `link.py`             |
| 3.8  | Update frontmatter `links` array (bidirectional)                          | `link.py`             |
| 3.9  | Implement `process_all_unlinked()` batch runner                           | `link.py`             |
| 3.10 | Capture 5+ additional real items → classify → link (15+ total wiki notes) | manual                |

### Key Functions

```python
# utils/embeddings.py
def get_model(): ...
def embed_text(text: str) -> np.ndarray: ...
def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float: ...
def find_top_k(query_vec, index, k=5) -> list[tuple[str, float]]: ...

# link.py
def embed_note(wiki_path: str) -> np.ndarray: ...
def find_similar(note_id: str, top_k: int = 5) -> list[tuple[str, float]]: ...
def auto_link_note(wiki_path: str, threshold: float = 0.75) -> list[str]: ...
def process_all_unlinked() -> int: ...
```

### Commands to Test

```bash
python link.py                        # batch: embed + link all
python link.py --note wiki/Projects/abc123.md   # single note
```

### Acceptance Criteria

- [ ] Embeddings computed per note (`.npy` files in `data/embeddings/`)
- [ ] `embeddings_index.json` updated after each embed
- [ ] Related notes auto-linked (no manual tagging)
- [ ] Links are bidirectional where possible
- [ ] **15+ real items** → organized, linked `wiki/` folder

### Estimated Effort

**6–8 hours**

---

## Phase 4 — Graph Builder + Interactive Visualization (Week 3)

**Goal:** Convert wiki notes and links into `graph.json` and render an interactive force-directed graph.

**Badge:** 🏅 The Cartographer

**Maps to:** Problem Statement Week 3 · Architecture §6.4

**Depends on:** Phase 3 (wiki notes with links)

### Tasks

#### 4.1 — Graph Data Model

| #   | Task                                                      | File             |
| --- | --------------------------------------------------------- | ---------------- |
| 4.1 | Parse wiki frontmatter + body                             | `build_graph.py` |
| 4.2 | Extract `[[wikilinks]]` from markdown body                | `build_graph.py` |
| 4.3 | Build in-memory nodes + edges                             | `build_graph.py` |
| 4.4 | Assign PARA colors to nodes                               | `build_graph.py` |
| 4.5 | Export clean `data/graph.json`                            | `build_graph.py` |
| 4.6 | Add metadata block (node_count, edge_count, generated_at) | `build_graph.py` |

#### 4.2 — Interactive Graph

| #    | Task                                            | File                                     |
| ---- | ----------------------------------------------- | ---------------------------------------- |
| 4.7  | Choose graph library (`streamlit-agraph` first) | `app.py` or standalone HTML              |
| 4.8  | Render force-directed graph from `graph.json`   | `static/graph_template.html` or `app.py` |
| 4.9  | Hover popups showing summary + content preview  | graph component                          |
| 4.10 | Drag-to-explore and zoom                        | graph component                          |
| 4.11 | Node pulse / visual styling by PARA category    | graph component                          |

### Key Functions

```python
# build_graph.py
def parse_wiki_note(path: str) -> dict: ...
def extract_wikilinks(body: str) -> list[str]: ...
def build_graph() -> dict: ...
def export_graph(output_path: str = "data/graph.json") -> str: ...
```

### Commands to Test

```bash
python build_graph.py
python -c "import json; g=json.load(open('data/graph.json')); print(g['metadata'])"

# Preview graph locally (minimal test app or Phase 5 app)
streamlit run app.py
```

### Graph Node Colors (PARA)

| Category  | Color     |
| --------- | --------- |
| Projects  | `#FF6B6B` |
| Areas     | `#4ECDC4` |
| Resources | `#45B7D1` |
| Archives  | `#96CEB4` |

### Acceptance Criteria

- [ ] Script builds nodes + edges from notes and exports clean JSON
- [ ] Interactive force-directed graph renders from that JSON
- [ ] Hover reveals note content (summary + preview)
- [ ] Drag + zoom work
- [ ] Built from your real notes, not dummy data

### Estimated Effort

**6–8 hours**

---

## Phase 5 — RAG Q&A + Streamlit App (Week 4)

**Goal:** Implement `ask()` for retrieval-augmented Q&A and assemble the full Streamlit UI.

**Badge:** 🏅 The Oracle

**Maps to:** Problem Statement Week 4 · Architecture §6.5, §6.6

**Depends on:** Phase 3 (embeddings), Phase 4 (graph.json)

### Tasks

#### 5.1 — RAG Q&A (`ask.py`)

| #   | Task                                                        | File     |
| --- | ----------------------------------------------------------- | -------- |
| 5.1 | Embed user question                                         | `ask.py` |
| 5.2 | Retrieve top-K similar notes from embeddings index          | `ask.py` |
| 5.3 | Apply minimum similarity floor (0.30)                       | `ask.py` |
| 5.4 | Build context from retrieved wiki notes                     | `ask.py` |
| 5.5 | Send context + question to LLM (Groq or Grok) for synthesis | `ask.py` |
| 5.6 | Return answer + source citations + confidence               | `ask.py` |
| 5.7 | Add CLI entry point for testing                             | `ask.py` |

#### 5.2 — Streamlit App (`app.py`)

| #    | Task                                                         | File                    |
| ---- | ------------------------------------------------------------ | ----------------------- |
| 5.8  | App layout: title, sidebar, tabs                             | `app.py`                |
| 5.9  | Tab 1: Brain Graph (load `graph.json`, render interactively) | `app.py`                |
| 5.10 | Tab 2: Ask Anything (input + button + answer display)        | `app.py`                |
| 5.11 | Sidebar: stats (note count, link count)                      | `app.py`                |
| 5.12 | Sidebar: "Run Pipeline" button                               | `app.py`, `pipeline.py` |
| 5.13 | Sidebar: quick capture form (optional)                       | `app.py`                |
| 5.14 | Click node → show full note in expander                      | `app.py`                |

#### 5.3 — Pipeline Orchestration

| #    | Task                                   | File          |
| ---- | -------------------------------------- | ------------- |
| 5.15 | Implement `run_full_pipeline()`        | `pipeline.py` |
| 5.16 | Wire pipeline to sidebar button in app | `app.py`      |

### Key Functions

```python
# ask.py
def retrieve_relevant_notes(question: str, top_k: int = 5) -> list[dict]: ...
def build_rag_prompt(question: str, notes: list[dict]) -> str: ...
def ask(question: str, top_k: int = 5) -> dict: ...

# pipeline.py
def run_full_pipeline() -> dict: ...
```

### Commands to Test

```bash
python ask.py "What do I know about Python?"
python ask.py "What projects am I working on?"

streamlit run app.py
```

### Acceptance Criteria

- [ ] `ask()` returns answers synthesized from your own notes (retrieval + LLM)
- [ ] Sources cited with note IDs and similarity scores
- [ ] One Streamlit app contains both the graph and the search bar
- [ ] Pipeline button runs classify → link → graph rebuild
- [ ] App runs locally without errors
- [ ] RAG synthesis works with configured LLM provider (Groq or Grok)

### Estimated Effort

**8–10 hours**

---

## Phase 6 — Local Module Testing

**Goal:** Verify each module works in isolation before running the full pipeline.

**Maps to:** Architecture §14 (Testing Strategy)

**Depends on:** Phase 5 (all modules implemented)

### Test Matrix

| Module                | Test                 | Command / Method                                                                        | Expected Result                            |
| --------------------- | -------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------ |
| `config.py`           | Import + paths exist | `python -c "import config; print(config.RAW_DIR)"`                                      | No errors                                  |
| `capture.py`          | Note capture         | `python capture.py --note "test note"`                                                  | File in `raw/` with timestamp + ID         |
| `capture.py`          | Link capture         | `python capture.py --link "https://example.com"`                                        | `.md` file with URL content                |
| `capture.py`          | File capture         | `python capture.py --file "sample.pdf"`                                                 | File copied to `raw/`                      |
| `classify.py`         | Single classify      | `python classify.py --file raw/...`                                                     | Wiki note in correct PARA folder           |
| `classify.py`         | Idempotency          | Run twice on same raw file                                                              | Second run skips                           |
| `link.py`             | Embed + link         | `python link.py --note wiki/...`                                                        | `.npy` created, wikilinks inserted         |
| `build_graph.py`      | Graph export         | `python build_graph.py`                                                                 | Valid `data/graph.json`                    |
| `ask.py`              | RAG query            | `python ask.py "question about your notes"`                                             | Answer + sources returned                  |
| `utils/llm.py`        | API connectivity     | `python -c "from utils.llm import call_llm; print(call_llm('hi'))"`                     | Groq or Grok responds (per `LLM_PROVIDER`) |
| `utils/embeddings.py` | Model load           | `python -c "from utils.embeddings import embed_text; print(embed_text('hello').shape)"` | (384,) vector                              |

### Optional: pytest Structure

```
tests/
├── test_capture.py       # ID format, filename pattern
├── test_classify.py      # frontmatter parsing
├── test_link.py          # wikilink insertion
├── test_build_graph.py   # node/edge counts
└── test_ask.py           # retrieval returns results
```

### Acceptance Criteria

- [ ] Every module passes its isolated tests
- [ ] No import errors across the project
- [ ] LLM API key works for configured provider (Groq or Grok)
- [ ] Embedding model downloads and encodes successfully
- [ ] All CLI entry points respond to `--help`

### Estimated Effort

**3–4 hours**

---

## Phase 7 — Local End-to-End Testing

**Goal:** Run the complete pipeline on real data and verify the full user journey locally.

**Maps to:** Problem Statement Final Deliverables · Architecture §7

**Depends on:** Phase 6 (modules verified)

### E2E Test Script

Run this sequence on **real data** (your own notes):

```bash
# Step 1: Capture fresh items
python capture.py --note "Your real idea here"
python capture.py --link "https://a-real-article-you-saved.com"
python capture.py --file "path/to/your/real-file.pdf"

# Step 2: Full pipeline
python classify.py
python link.py
python build_graph.py

# Step 3: Ask questions
python ask.py "What topics have I captured?"
python ask.py "What are my active projects?"
python ask.py "Summarize my notes about [specific topic you captured]"

# Step 4: Streamlit UI
streamlit run app.py
```

### E2E Verification Checklist

| Step     | Check                                                         | Pass? |
| -------- | ------------------------------------------------------------- | ----- |
| Capture  | 10+ items in `raw/` with timestamp + UUID                     | ☐     |
| Classify | Every raw file has a wiki counterpart                         | ☐     |
| Classify | PARA folders populated (Projects, Areas, Resources, Archives) | ☐     |
| Link     | Embeddings exist for all wiki notes                           | ☐     |
| Link     | At least some notes have auto-generated wikilinks             | ☐     |
| Graph    | `graph.json` node count matches wiki note count               | ☐     |
| Graph    | Edges reflect wikilinks                                       | ☐     |
| Graph UI | Force-directed layout renders                                 | ☐     |
| Graph UI | Hover shows note preview                                      | ☐     |
| Graph UI | Drag and zoom work                                            | ☐     |
| Ask      | Returns relevant answer from your notes                       | ☐     |
| Ask      | Sources listed with note references                           | ☐     |
| Ask      | Handles "I don't know" for unrelated questions                | ☐     |
| App      | Both tabs (Graph + Ask) functional                            | ☐     |
| App      | Pipeline button rebuilds graph                                | ☐     |

### Performance Sanity Checks

| Operation         | Target | Actual |
| ----------------- | ------ | ------ |
| Single capture    | < 1s   |        |
| Classify one note | 1–3s   |        |
| Embed one note    | 0.5–2s |        |
| Build graph       | < 1s   |        |
| ask() end-to-end  | 3–8s   |        |
| Graph render      | 1–3s   |        |

### Acceptance Criteria

- [ ] Full pipeline works: capture → classify → link → graph → ask
- [ ] Tested on 15+ real items (not dummy data)
- [ ] Streamlit app runs locally with no errors
- [ ] At least 3 real questions answered correctly by `ask()`

### Estimated Effort

**3–4 hours**

---

## Phase 8 — Deploy to Public URL

**Goal:** Ship the Streamlit app to Streamlit Cloud (or Hugging Face Spaces) with a public URL.

**Maps to:** Problem Statement Week 4.2 · Architecture §10

**Depends on:** Phase 7 (local E2E passes)

### Pre-Deploy Checklist

| #   | Item                     | Action                                                                   |
| --- | ------------------------ | ------------------------------------------------------------------------ |
| 8.1 | Clean `requirements.txt` | Pin major versions; remove unused deps                                   |
| 8.2 | Write `README.md`        | Setup, usage, architecture overview, live URL                            |
| 8.3 | Prepare demo data        | Commit sample `wiki/` + `data/graph.json` (sanitized)                    |
| 8.4 | Exclude personal data    | Gitignore `raw/` or commit only demo captures                            |
| 8.5 | Create GitHub repo       | Push all code                                                            |
| 8.6 | Configure secrets        | `LLM_PROVIDER`, `GROQ_API_KEY`, `XAI_API_KEY` in Streamlit Cloud secrets |
| 8.7 | Set main file            | `app.py`                                                                 |
| 8.8 | Deploy                   | Connect repo → Streamlit Cloud → Deploy                                  |

### Deployment Steps (Streamlit Cloud)

```
1. Push repo to GitHub (public repo)
2. Go to https://share.streamlit.io
3. Click "New app" → select repo, branch, main file: app.py
4. Advanced settings → Secrets:

   LLM_PROVIDER = "groq"          # or "grok"
   GROQ_API_KEY = "gsk_your_key_here"
   XAI_API_KEY = "xai_your_key_here"   # required when LLM_PROVIDER=grok

5. Deploy → wait for build
6. Copy public URL (e.g. https://secondself.streamlit.app)
7. Add URL to README.md
```

### Alternative: Hugging Face Spaces

```
1. Create new Space → SDK: Streamlit
2. Push code to Space repo
3. Add `LLM_PROVIDER`, `GROQ_API_KEY`, and/or `XAI_API_KEY` in Space Settings → Repository secrets
4. Space auto-builds and provides URL
```

### Files Required in Repo for Deploy

```
app.py
requirements.txt
README.md
config.py
ask.py
build_graph.py
classify.py
link.py
capture.py
pipeline.py
utils/
wiki/              # demo notes (sanitized)
data/graph.json    # pre-built graph
data/embeddings/   # pre-computed (or rebuild on first run)
```

### Acceptance Criteria

- [ ] Public GitHub repo with clean README + setup instructions
- [ ] App deployed and accessible via public URL
- [ ] No secrets committed to repo
- [ ] Build completes without dependency errors

### Estimated Effort

**2–3 hours**

---

## Phase 9 — Final Production Testing

**Goal:** Verify the deployed app works end-to-end on the live URL for anyone who opens it.

**Maps to:** Problem Statement Final Deliverables

**Depends on:** Phase 8 (deployed)

### Production Test Checklist

| #    | Test               | How                                                     | Pass? |
| ---- | ------------------ | ------------------------------------------------------- | ----- |
| 9.1  | App loads          | Open public URL in browser                              | ☐     |
| 9.2  | Graph renders      | Brain Graph tab shows nodes + edges                     | ☐     |
| 9.3  | Graph interaction  | Hover, drag, zoom all work                              | ☐     |
| 9.4  | Ask tab works      | Type question → get answer                              | ☐     |
| 9.5  | Sources displayed  | Answer includes note citations                          | ☐     |
| 9.6  | Unrelated question | Ask something not in notes → honest "don't know"        | ☐     |
| 9.7  | Mobile check       | Open URL on phone (basic layout)                        | ☐     |
| 9.8  | Cold start         | First load after deploy completes in < 60s              | ☐     |
| 9.9  | README accuracy    | Follow setup instructions from scratch on a fresh clone | ☐     |
| 9.10 | URL in README      | Live link works and matches deployed app                | ☐     |

### Final Deliverables Checklist

- [ ] Public **GitHub repo** with clean README + setup instructions
- [ ] **Live deployed URL** — interactive graph + ask-your-brain search, both working
- [ ] End-to-end flow verified: capture → classify → link → graph → ask
- [ ] All 4 weekly milestones complete:
  - [ ] 🏅 The Archivist (Capture Pipeline)
  - [ ] 🏅 The Librarian (Self-Organizing Wiki)
  - [ ] 🏅 The Cartographer (Living Brain)
  - [ ] 🏅 The Oracle (SecondSelf deployment)

### Estimated Effort

**2–3 hours**

---

## Master Timeline

| Phase | Description        | Effort   | Cumulative |
| ----- | ------------------ | -------- | ---------- |
| 0     | Setup              | 2–3 hrs  | 2–3 hrs    |
| 1     | Capture            | 4–6 hrs  | 6–9 hrs    |
| 2     | Classify           | 5–7 hrs  | 11–16 hrs  |
| 3     | Auto-link          | 6–8 hrs  | 17–24 hrs  |
| 4     | Graph              | 6–8 hrs  | 23–32 hrs  |
| 5     | RAG + App          | 8–10 hrs | 31–42 hrs  |
| 6     | Local module tests | 3–4 hrs  | 34–46 hrs  |
| 7     | Local E2E tests    | 3–4 hrs  | 37–50 hrs  |
| 8     | Deploy             | 2–3 hrs  | 39–53 hrs  |
| 9     | Prod tests         | 2–3 hrs  | 41–56 hrs  |

**Total estimated effort: 40–56 hours** (matches a 4-week part-time build)

---

## Quick Reference — Commands by Phase

```bash
# Phase 0
python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt
python -c "import config; print(config.LLM_PROVIDER)"

# Phase 0 — verify LLM provider (run after Phase 2 implements utils/llm.py)
# Groq (default)
set LLM_PROVIDER=groq && python -c "from utils.llm import call_llm; print(call_llm('ping'))"
# Grok (xAI)
set LLM_PROVIDER=grok && python -c "from utils.llm import call_llm; print(call_llm('ping'))"

# Phase 1
python capture.py --note "..."
python capture.py --link "https://..."
python capture.py --file "path/to/file"

# Phase 2
python classify.py

# Phase 3
python link.py

# Phase 4
python build_graph.py

# Phase 5
python ask.py "Your question here"
streamlit run app.py

# Phase 7 (full pipeline)
python classify.py && python link.py && python build_graph.py

# Phase 8
git push origin main   # triggers Streamlit Cloud deploy
```

---

## Risk Mitigation per Phase

| Phase | Risk                                | Mitigation                                                                                                                            |
| ----- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| 0     | Groq API key invalid                | Test with `call_llm("hello")` when `LLM_PROVIDER=groq`; verify at [console.groq.com](https://console.groq.com)                        |
| 0     | Grok (xAI) API key invalid          | Test with `call_llm("hello")` when `LLM_PROVIDER=grok`; verify at [console.x.ai](https://console.x.ai)                                |
| 0     | Wrong provider selected             | `config.py` validates `LLM_PROVIDER` at import; raise clear error if key missing for chosen provider                                  |
| 0     | Provider rate limits                | Groq free tier has RPM limits; Grok has separate quotas — add exponential backoff in `utils/llm.py`                                   |
| 1     | Link fetch fails (blocked URL)      | Store URL + error message; don't crash                                                                                                |
| 2     | LLM returns invalid JSON            | Retry with stricter prompt; log to `classify_errors.log`; works for both Groq and Grok                                                |
| 2     | Groq vs Grok JSON format drift      | Normalize response in `call_llm_json()` — strip markdown fences, parse with fallback                                                  |
| 3     | Embedding model slow on first run   | Pre-download in Phase 0: `python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"` |
| 3     | No links found (threshold too high) | Lower `SIMILARITY_LINK_THRESHOLD` in `config.py` to 0.65                                                                              |
| 4     | Graph too cluttered                 | Filter by PARA category; limit node labels                                                                                            |
| 5     | RAG hallucination                   | Strict "answer ONLY from notes" prompt; show sources                                                                                  |
| 5     | Provider latency differences        | Groq tends faster; Grok may be slower — show spinner in Streamlit; cache recent answers                                               |
| 8     | Streamlit build fails               | Pin all deps; test `pip install` in fresh venv                                                                                        |
| 8     | Secrets not loaded                  | Use `st.secrets` fallback to `os.getenv` in `config.py`; document both providers in README                                            |
| 8     | Deployed app uses wrong LLM         | Set `LLM_PROVIDER` explicitly in Streamlit secrets — don't rely on local `.env`                                                       |

---

_Next step: Generate [`edge-case.md`](edge-case.md) for corner scenarios, then implement **Phase 0**._
