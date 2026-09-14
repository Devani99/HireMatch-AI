"""
pdf_service.py
--------------
PDF file validation and text extraction.

All PDF operations are isolated in this module.
The Streamlit UI passes UploadedFile objects here and receives
clean extracted text strings back.
"""

from __future__ import annotations

import io
import logging
import re
from typing import NamedTuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_FILE_SIZE_BYTES: int = 5 * 1024 * 1024   # 5 MB
MAX_FILE_SIZE_LABEL: str = "5 MB"
ALLOWED_EXTENSION: str = "pdf"
MIN_EXTRACTABLE_CHARS: int = 50             # Minimum chars to be considered non-empty


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

class PdfExtractionResult(NamedTuple):
    success: bool
    text: str          # Extracted text (empty string on failure)
    error: str         # Human-readable error message (empty string on success)
    page_count: int    # Number of pages found (0 on failure)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _has_pdf_extension(filename: str) -> bool:
    return filename.lower().strip().endswith(f".{ALLOWED_EXTENSION}")


def _get_file_size(uploaded_file) -> int:
    """Return byte size of a Streamlit UploadedFile."""
    # Streamlit UploadedFile exposes .size directly
    if hasattr(uploaded_file, "size"):
        return uploaded_file.size
    # Fallback: read and measure
    data = uploaded_file.read()
    uploaded_file.seek(0)
    return len(data)


# ---------------------------------------------------------------------------
# Public validation — called before extraction
# ---------------------------------------------------------------------------

def validate_pdf_upload(uploaded_file) -> str | None:
    """
    Validate a Streamlit UploadedFile before extraction.

    Returns:
        None if the file is valid.
        A human-readable error string if the file is invalid.
    """
    if uploaded_file is None:
        return None  # Caller handles 'no file' case separately

    # Extension check
    if not _has_pdf_extension(uploaded_file.name):
        return "Please upload a PDF file only."

    # Size check
    size = _get_file_size(uploaded_file)
    if size > MAX_FILE_SIZE_BYTES:
        size_mb = size / (1024 * 1024)
        return (
            f"The file size ({size_mb:.1f} MB) exceeds the {MAX_FILE_SIZE_LABEL} limit. "
            f"Please upload a smaller PDF."
        )

    return None


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def extract_pdf_text(uploaded_file) -> PdfExtractionResult:
    """
    Extract all text from a Streamlit UploadedFile containing a PDF.

    Steps:
        1. Read file bytes.
        2. Attempt to open with pypdf.
        3. Extract text from every page.
        4. Combine, clean, and return.

    Returns:
        PdfExtractionResult with success flag, text, error message, and page count.
    """
    try:
        import pypdf  # lazy import — only required when processing a PDF
    except ImportError:
        logger.error("pypdf is not installed. Run: pip install pypdf")
        return PdfExtractionResult(
            success=False,
            text="",
            error="PDF processing library is not available. Please contact support.",
            page_count=0,
        )

    # --- Read bytes ---
    try:
        uploaded_file.seek(0)
        file_bytes = uploaded_file.read()
    except Exception as exc:
        logger.exception("Failed to read uploaded file bytes: %s", exc)
        return PdfExtractionResult(
            success=False,
            text="",
            error="The uploaded file could not be read. Please upload a valid PDF.",
            page_count=0,
        )

    # --- Open PDF ---
    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    except pypdf.errors.PdfStreamError as exc:
        logger.warning("PDF stream error (corrupted?): %s", exc)
        return PdfExtractionResult(
            success=False,
            text="",
            error="The uploaded file could not be read. Please upload a valid PDF.",
            page_count=0,
        )
    except pypdf.errors.FileNotDecryptedError:
        logger.warning("PDF is password-protected")
        return PdfExtractionResult(
            success=False,
            text="",
            error=(
                "This PDF is password-protected. "
                "Please remove the password and upload again."
            ),
            page_count=0,
        )
    except Exception as exc:
        logger.exception("Unexpected PDF open error: %s", exc)
        return PdfExtractionResult(
            success=False,
            text="",
            error="The uploaded file could not be read. Please upload a valid PDF.",
            page_count=0,
        )

    page_count = len(reader.pages)

    # --- Extract text from pages ---
    page_texts: list[str] = []
    for i, page in enumerate(reader.pages):
        try:
            page_text = page.extract_text() or ""
            page_texts.append(page_text)
        except Exception as exc:
            logger.warning("Could not extract text from page %d: %s", i, exc)
            page_texts.append("")  # Skip failed pages, continue

    raw_text = "\n".join(page_texts)

    # --- Clean the extracted text ---
    cleaned = _clean_text(raw_text)

    # --- Check for empty result ---
    if len(cleaned.strip()) < MIN_EXTRACTABLE_CHARS:
        return PdfExtractionResult(
            success=False,
            text="",
            error=(
                "No readable text was found in this PDF. "
                "This PDF does not contain readable text. "
                "Please upload a text-based PDF."
            ),
            page_count=page_count,
        )

    return PdfExtractionResult(
        success=True,
        text=cleaned,
        error="",
        page_count=page_count,
    )


# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------

def _clean_text(raw: str) -> str:
    """
    Remove excessive whitespace while preserving meaningful structure.
    """
    if not raw:
        return ""

    # Normalize Windows line endings
    text = raw.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse runs of more than 2 consecutive blank lines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Collapse multiple spaces on a single line (but not leading indentation)
    lines = text.split("\n")
    cleaned_lines = [re.sub(r" {2,}", " ", line) for line in lines]
    text = "\n".join(cleaned_lines)

    return text.strip()


# ---------------------------------------------------------------------------
# File info helper for the UI
# ---------------------------------------------------------------------------

def format_file_info(uploaded_file) -> dict[str, str]:
    """
    Return a dict of display-ready file metadata strings.
    """
    size_bytes = _get_file_size(uploaded_file)
    if size_bytes < 1024:
        size_str = f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        size_str = f"{size_bytes / 1024:.1f} KB"
    else:
        size_str = f"{size_bytes / (1024 * 1024):.2f} MB"

    return {
        "File name": uploaded_file.name,
        "File size": size_str,
        "Status": "Ready",
    }
