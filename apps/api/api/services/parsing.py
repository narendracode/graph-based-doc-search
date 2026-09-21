"""PDF parsing/chunking. Uses `unstructured`'s "auto" strategy, which extracts native
text where present and falls back to local Tesseract OCR per page for scanned content
— no bespoke OCR-fallback logic needed here.
"""

from unstructured.chunking.title import chunk_by_title
from unstructured.partition.pdf import partition_pdf

MAX_CHUNK_CHARS = 1500


def parse_and_chunk(file_path: str) -> list[str]:
    elements = partition_pdf(filename=file_path, strategy="auto")
    chunks = chunk_by_title(elements, max_characters=MAX_CHUNK_CHARS)
    texts = [str(chunk).strip() for chunk in chunks]
    return [t for t in texts if t]
