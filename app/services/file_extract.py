"""
eaiou — File extraction service
MIME sniffing (magic bytes), text extraction, metadata exclusion.
Supports: PDF (pypdf), DOCX (python-docx), plain text (UTF-8).
"""
import hashlib
import io
import os
import pathlib
import zipfile

from fastapi import HTTPException

UPLOAD_DIR = pathlib.Path(os.getenv("UPLOAD_DIR", "/var/eaiou/uploads"))
MAX_FILE_SIZE = 10 * 1024 * 1024   # 10 MB
MAX_USER_FILES = 100                 # soft cap per user


# ── MIME sniffing ─────────────────────────────────────────────────────────────

def sniff_mime(content: bytes) -> str | None:
    """Return MIME type from magic bytes, or None if unrecognised."""
    if content[:4] == b"%PDF":
        return "application/pdf"
    if content[:2] == b"PK":
        # DOCX / XLSX / PPTX are all ZIP; check for word/document.xml to distinguish
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                if "word/document.xml" in zf.namelist():
                    return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        except Exception:
            pass
    # Plain text: try UTF-8 decode on first 512 bytes
    try:
        content[:512].decode("utf-8")
        return "text/plain"
    except (UnicodeDecodeError, ValueError):
        pass
    return None


def validate_file(content: bytes, filename: str) -> str:
    """
    Validate size and MIME type.  Returns the detected MIME string.
    Raises HTTPException 413 or 415 on failure.
    """
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum 10 MB.")
    mime = sniff_mime(content)
    allowed = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
    }
    if mime not in allowed:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type. Upload PDF, DOCX, or plain text (.txt).",
        )
    return mime


# ── Text extraction (metadata excluded) ──────────────────────────────────────

def _normalize_math_unicode(text: str) -> str:
    """
    Fix two pypdf math-font artifacts:
    1. /uXXXX(X) literal escape sequences → actual Unicode characters
    2. Mathematical Italic/Bold/Script symbols (U+1D400–U+1D7FF) → ASCII via NFKC
    """
    import re, unicodedata

    def _sub(m):
        try:
            return chr(int(m.group(1), 16))
        except (ValueError, OverflowError):
            return m.group(0)

    text = re.sub(r'/u([0-9A-Fa-f]{4,5})', _sub, text)
    return unicodedata.normalize('NFKC', text)


def _extract_pdf(content: bytes) -> str:
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(content))
    # reader.metadata is never accessed — only page body text
    parts = []
    for page in reader.pages:
        text = page.extract_text() or ""
        parts.append(_normalize_math_unicode(text))
    return "\n".join(parts)


def _extract_docx(content: bytes) -> str:
    import docx
    doc = docx.Document(io.BytesIO(content))
    # doc.core_properties is never accessed
    # Only body paragraphs — no headers, footers, comments, tracked changes
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def extract_text(content: bytes, mime_type: str) -> str:
    if mime_type == "application/pdf":
        return _extract_pdf(content)
    if mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return _extract_docx(content)
    # text/plain
    return content.decode("utf-8", errors="replace")


# ── Storage helpers ───────────────────────────────────────────────────────────

def compute_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _ext_for(mime_type: str) -> str:
    return {
        "application/pdf": ".pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "text/plain": ".txt",
    }.get(mime_type, ".bin")


def stored_path(user_id: int, sha256: str, mime_type: str) -> pathlib.Path:
    """Absolute path: UPLOAD_DIR/{user_id}/{sha256[:2]}/{sha256}{ext}"""
    ext = _ext_for(mime_type)
    return UPLOAD_DIR / str(user_id) / sha256[:2] / f"{sha256}{ext}"


def stored_rel(user_id: int, sha256: str, mime_type: str) -> str:
    """Relative path string stored in DB (relative to UPLOAD_DIR)."""
    p = stored_path(user_id, sha256, mime_type)
    return str(p.relative_to(UPLOAD_DIR))


def save_to_disk(content: bytes, path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
