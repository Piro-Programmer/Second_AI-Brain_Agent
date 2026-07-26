import json
import lib.config as config
from groq import Groq

client = Groq(api_key=config.GROQ_API_KEY)

def call_llm(prompt: str, system: str = "", json_mode: bool = True, temperature: float = 0.1) -> str:
    """Wrapper to call Groq API."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    kwargs = {
        "model": config.GROQ_MODEL,
        "messages": messages,
        "temperature": temperature
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
        
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content

def classify_content(text: str) -> dict:
    """Send text to LLM and get {para, tags, summary}."""
    system_prompt = (
        "You are an AI Librarian that organizes notes using the PARA method.\n"
        "Output MUST be valid JSON containing exactly these keys:\n"
        "- 'para': Exactly one of 'Projects', 'Areas', 'Resources', 'Archives'.\n"
        "- 'tags': Array of 2-5 relevant string tags.\n"
        "- 'summary': A one-line summary of the content.\n"
        "If you are unsure of the category, default to 'Resources'.\n"
    )
    
    # Truncate text if it's too long
    max_length = 15000
    truncated_text = text[:max_length]
    
    prompt = f"Please classify the following content:\n\n{truncated_text}"
    
    response_text = call_llm(prompt, system=system_prompt, json_mode=True, temperature=0.1)
    
    try:
        data = json.loads(response_text)
        # Enforce PARA category constraint
        if data.get("para") not in config.PARA_CATEGORIES:
            data["para"] = "Resources"
        return data
    except json.JSONDecodeError:
        return {
            "para": "Resources",
            "tags": ["unclassified"],
            "summary": "Failed to extract summary."
        }
        
def synthesize_answer(context: str, question: str) -> str:
    """Synthesize RAG answer using Groq LLM based on retrieved notes."""
    system_prompt = (
        "You are SecondSelf, answering from the user's personal knowledge base. "
        "Use ONLY the provided notes. If the answer isn't in the notes, say so. "
        "Cite sources as [note-id]."
    )
    prompt = f"Notes:\n{context}\n\nQuestion: {question}"
    return call_llm(prompt, system=system_prompt, json_mode=False, temperature=0.3)
