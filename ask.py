import os
import sys
import argparse
import glob
import frontmatter
import lib.config as config
from lib.embeddings import embed_text, cosine_similarity, load_embeddings
from lib.llm import synthesize_answer

EMBEDDINGS_FILE = os.path.join(config.DATA_DIR, "embeddings.pkl")

def get_wiki_note_by_id() -> dict:
    """Scan wiki directory and return mapping of note_id -> {path, post, summary, para}."""
    mapping = {}
    search_pattern = os.path.join(config.WIKI_DIR, "**", "*.md")
    for filepath in glob.glob(search_pattern, recursive=True):
        try:
            post = frontmatter.load(filepath)
            note_id = post.get("id")
            if note_id:
                mapping[str(note_id)] = {
                    "id": str(note_id),
                    "path": filepath,
                    "post": post,
                    "summary": post.get("summary", "Untitled Note"),
                    "para": post.get("para", "Resources"),
                    "content": post.content
                }
        except Exception as e:
            continue
    return mapping

def retrieve_relevant_notes(question: str, top_k: int = 5) -> list[dict]:
    """Retrieve top-K notes exceeding similarity floor for a question."""
    embeddings_db = load_embeddings(EMBEDDINGS_FILE)
    if not embeddings_db:
        print("Warning: No embeddings found in embeddings.pkl. Run pipeline link or process first.")
        return []
        
    q_vec = embed_text(question)
    wiki_notes = get_wiki_note_by_id()
    
    scored_notes = []
    for note_id, note_vec in embeddings_db.items():
        if note_id not in wiki_notes:
            continue
        score = cosine_similarity(q_vec, note_vec)
        if score >= config.SIMILARITY_RETRIEVAL_MIN:
            note_info = wiki_notes[note_id]
            scored_notes.append({
                "id": note_id,
                "summary": note_info["summary"],
                "relevance_score": float(score),
                "para": note_info["para"],
                "content": note_info["content"]
            })
            
    # Sort descending by relevance score
    scored_notes.sort(key=lambda x: x["relevance_score"], reverse=True)
    return scored_notes[:top_k]

def build_rag_prompt_context(notes: list[dict], max_chars: int = 24000) -> str:
    """Build formatted context string from retrieved notes, enforcing length guardrails."""
    context_blocks = []
    current_chars = 0
    
    for note in notes:
        block = f"Note ID: [{note['id']}]\nCategory: {note['para']}\nSummary: {note['summary']}\nContent:\n{note['content']}\n"
        if current_chars + len(block) > max_chars:
            remaining = max_chars - current_chars
            if remaining > 100:
                block = block[:remaining] + "\n...[truncated due to context limits]\n"
                context_blocks.append(block)
            break
        context_blocks.append(block)
        current_chars += len(block)
        
    return "\n---\n".join(context_blocks)

def ask(question: str, top_k: int = 5) -> dict:
    """End-to-end RAG Q&A pipeline: retrieve notes and synthesize answer via LLM."""
    retrieved = retrieve_relevant_notes(question, top_k=top_k)
    
    if not retrieved:
        return {
            "answer": "I don't have notes about that in your knowledge base.",
            "sources": []
        }
        
    context_str = build_rag_prompt_context(retrieved)
    answer = synthesize_answer(context_str, question)
    
    # Strip content from returned sources list to keep response clean
    sources = [
        {
            "id": n["id"],
            "summary": n["summary"],
            "relevance_score": round(n["relevance_score"], 4),
            "para": n["para"]
        }
        for n in retrieved
    ]
    
    return {
        "answer": answer,
        "sources": sources
    }

def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Ask SecondSelf a question using Retrieval-Augmented Q&A.")
    parser.add_argument("question", nargs="?", help="The question to ask your second brain")
    parser.add_argument("-k", "--top-k", type=int, default=5, help="Number of relevant notes to retrieve")
    args = parser.parse_args()
    
    if not args.question:
        print("Please provide a question. Example:\n  python ask.py \"What do I know about Python?\"")
        sys.exit(1)
        
    print(f"\nQuerying SecondSelf: \"{args.question}\"...\n")
    result = ask(args.question, top_k=args.top_k)
    
    print("=" * 60)
    print("ANSWER:")
    print("=" * 60)
    print(result["answer"])
    print("\n" + "=" * 60)
    print(f"SOURCES CITED ({len(result['sources'])} notes):")
    print("=" * 60)
    if result["sources"]:
        for idx, src in enumerate(result["sources"], 1):
            print(f"{idx}. [{src['para']}] {src['summary']} (Score: {src['relevance_score']})")
            print(f"   ID: {src['id']}")
    else:
        print("None")
    print()

if __name__ == "__main__":
    main()
