import os
import requests
from bs4 import BeautifulSoup
try:
    from pypdf import PdfReader
except ImportError:
    import pypdf

def fetch_link_content(url: str) -> dict:
    """Fetch URL and extract title and main text."""
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title = soup.title.string.strip() if soup.title and soup.title.string else "Untitled"
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
            
        text = soup.get_text(separator='\n')
        # collapse whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return {
            "title": title,
            "text": text,
            "url": url
        }
    except Exception as e:
        return {
            "title": "Error fetching URL",
            "text": f"Could not fetch content from {url}. Error: {str(e)}",
            "url": url
        }

def extract_pdf_text(file_path: str) -> str:
    """Extract text from a PDF file."""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text
    except Exception as e:
        return f"Error extracting PDF text: {str(e)}"

def detect_source_type(input_value: str) -> str:
    """Helper to detect if a string is a url, file, or note."""
    if input_value.startswith("http://") or input_value.startswith("https://"):
        return "link"
    if os.path.exists(input_value):
        return "file"
    return "note"
