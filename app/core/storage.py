import tempfile
from pathlib import Path

from pypdf import PdfReader


CHUNK_SIZE = 512
CHUNK_OVERLAP = 50


def extract_text_from_pdf(file_path: str | Path) -> str:
    reader = PdfReader(file_path)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n\n".join(pages)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    import tiktoken

    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    chunks = []
    start = 0

    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        chunk_text = enc.decode(chunk_tokens)
        if chunk_text.strip():
            chunks.append(chunk_text)
        start += chunk_size - overlap

    return chunks


def save_temp_file(file_bytes: bytes, suffix: str = ".pdf") -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_bytes)
        return tmp.name
