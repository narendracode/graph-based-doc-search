"""Document parsing/chunking. Uses `unstructured`'s format auto-detection (`partition`)
so PDF, DOCX, XLSX, CSV, TXT, and PPTX all go through one path — for PDFs specifically
it still runs "auto" strategy, which extracts native text where present and falls back
to local Tesseract OCR per page for scanned content. No bespoke per-format logic here.
"""

from unstructured.chunking.title import chunk_by_title
from unstructured.partition.auto import partition

MAX_CHUNK_CHARS = 1500


def parse_and_chunk(file_path: str) -> list[str]:
    elements = partition(filename=file_path, strategy="auto")
    chunks = chunk_by_title(elements, max_characters=MAX_CHUNK_CHARS)
    texts = [str(chunk).strip() for chunk in chunks]
    return [t for t in texts if t]
