import hashlib
import uuid
from pathlib import Path

from api.config import get_settings

settings = get_settings()


def _storage_root() -> Path:
    root = Path(settings.storage_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def save_upload(document_id: uuid.UUID, filename: str, data: bytes) -> tuple[str, str]:
    """Persist raw upload bytes to disk. Returns (storage_path, sha256_checksum)."""
    suffix = Path(filename).suffix
    dest = _storage_root() / f"{document_id}{suffix}"
    dest.write_bytes(data)
    checksum = hashlib.sha256(data).hexdigest()
    return str(dest), checksum


def delete_file(storage_path: str) -> None:
    path = Path(storage_path)
    if path.exists():
        path.unlink()


def read_file(storage_path: str) -> bytes:
    return Path(storage_path).read_bytes()
