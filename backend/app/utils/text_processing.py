import re
import unicodedata
from typing import Tuple

def normalize_legal_text(raw_text: str) -> str:
    """
    Safely cleans and normalizes legal text without stripping legal meaning,
    negations, monetary amounts, or clause identifiers.
    """
    if not raw_text:
        return ""

    # Normalize unicode to standard form NFC
    text = unicodedata.normalize("NFC", raw_text)

    # Standardize curly quotes and apostrophes to standard ASCII representations
    quote_map = {
        '“': '"', '”': '"', '„': '"', '‟': '"',
        '‘': "'", '’': "'", '‚': "'", '‛': "'",
        '—': ' - ', '–': ' - ', '−': ' - '
    }
    for orig, rep in quote_map.items():
        text = text.replace(orig, rep)

    # Remove non-printable control characters except standard tabs and newlines
    text = "".join(ch for ch in text if ch in ("\n", "\r", "\t") or unicodedata.category(ch)[0] != "C")

    # Fix hyphenation across line breaks (e.g., "in- \n demnify" -> "indemnify")
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)

    # Normalize excessive carriage returns and tabs
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r'\t+', ' ', text)

    # Normalize multiple horizontal spaces to single space, but preserve paragraph breaks
    lines = []
    for line in text.split("\n"):
        clean_line = re.sub(r'[^\S\n]+', ' ', line).strip()
        lines.append(clean_line)

    # Join lines: collapse multiple blank lines to a double newline (paragraph boundary)
    normalized = "\n".join(lines)
    normalized = re.sub(r'\n{3,}', '\n\n', normalized)

    return normalized.strip()

def validate_text_content(text: str, min_chars: int = 25) -> Tuple[bool, str]:
    """
    Verifies that extracted text is not empty or merely OCR garbage/whitespace.
    """
    if not text or not text.strip():
        return False, "Document contains no extractable text."
    
    clean = re.sub(r'\s+', '', text)
    if len(clean) < min_chars:
        return False, f"Extracted text is too short ({len(clean)} characters). Minimum required is {min_chars} characters."

    # Check if there are alphanumeric characters
    alnum_count = sum(1 for c in clean if c.isalnum())
    if alnum_count < 10:
        return False, "Extracted content contains insufficient alphanumeric text to constitute a valid legal document."

    return True, ""
