"""
services/document_service.py — Document parsing and text extraction (PDF, DOCX, TXT, OCR).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


def extract_text_from_file(file_path: str, mime_type: str) -> Tuple[str, bool, Dict[str, Any]]:
    """
    Extract text from an uploaded document.
    Returns:
        (extracted_text, ocr_used, metadata)
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = path.suffix.lower()
    text = ""
    ocr_used = False
    metadata: Dict[str, Any] = {"file_size": path.stat().st_size, "extension": ext}

    try:
        if ext == ".txt":
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()

        elif ext == ".pdf":
            text, ocr_used, pdf_meta = _extract_from_pdf(path)
            metadata.update(pdf_meta)

        elif ext in [".docx", ".doc"]:
            text, docx_meta = _extract_from_docx(path)
            metadata.update(docx_meta)

        elif ext in [".jpg", ".jpeg", ".png", ".tiff", ".bmp"]:
            text = _extract_from_image(path)
            ocr_used = True
            metadata["is_image"] = True

        else:
            # Fallback to plain text read
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()

    except Exception as exc:
        logger.error("Error extracting text from %s: %s", file_path, exc)
        raise RuntimeError(f"Text extraction failed: {exc}") from exc

    return text.strip(), ocr_used, metadata


def _extract_from_pdf(path: Path) -> Tuple[str, bool, Dict[str, Any]]:
    """Extract text from PDF using PyMuPDF (fitz), with OCR fallback for scanned pages."""
    ocr_used = False
    page_count = 0
    full_text = []

    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(path))
        page_count = len(doc)

        for page_num in range(page_count):
            page = doc[page_num]
            page_text = page.get_text()

            # If page text is very short/empty, run OCR on the page pixmap
            if len(page_text.strip()) < 30:
                pix = page.get_pixmap()
                img_bytes = pix.tobytes("png")
                ocr_text = _run_ocr_on_bytes(img_bytes)
                if len(ocr_text.strip()) > len(page_text.strip()):
                    page_text = ocr_text
                    ocr_used = True

            full_text.append(page_text)

        doc.close()
    except ImportError:
        logger.warning("PyMuPDF not available, trying pdfminer or raw read")
        with open(path, "r", encoding="latin-1", errors="ignore") as f:
            full_text = [f.read()]

    return "\n\n".join(full_text), ocr_used, {"pages": page_count}


def _extract_from_docx(path: Path) -> Tuple[str, Dict[str, Any]]:
    """Extract text from docx file."""
    import docx
    doc = docx.Document(str(path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs), {"paragraphs": len(paragraphs)}


def _extract_from_image(path: Path) -> str:
    """Extract text from image using pytesseract."""
    try:
        from PIL import Image
        import pytesseract

        img = Image.open(str(path))
        text = pytesseract.image_to_string(img)
        return text
    except Exception as exc:
        logger.warning("OCR failed on image %s: %s", path, exc)
        return ""


def _run_ocr_on_bytes(image_bytes: bytes) -> str:
    """Run pytesseract OCR on in-memory image bytes."""
    try:
        import io
        from PIL import Image
        import pytesseract

        img = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(img)
    except Exception as exc:
        logger.warning("OCR failed on page pixmap: %s", exc)
        return ""
