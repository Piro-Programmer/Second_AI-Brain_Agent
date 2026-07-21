import json
import lib.config as config
from groq import Groq

client = Groq(api_key=config.GROQ_API_KEY)

def call_llm(prompt: str, system: str = "") -> str:
    """Wrapper to call Groq API."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    response = client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.1
    )
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
    
    response_text = call_llm(prompt, system=system_prompt)
    
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
    # Stub for Week 4
    pass
