"""Rasterize a generated sticker-sheet PDF to a PNG -- the "rendered preview" a future GUI
shows before printing. Engine-side so every frontend reuses it.
"""

from __future__ import annotations

import fitz  # PyMuPDF


def render_page(pdf_bytes: bytes, page: int = 0, dpi: int = 150) -> bytes:
    """Return PNG bytes of ``page`` of the given PDF, rendered at ``dpi``."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        pix = doc[page].get_pixmap(dpi=dpi)
        return pix.tobytes("png")
    finally:
        doc.close()


def page_count(pdf_bytes: bytes) -> int:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        return doc.page_count
    finally:
        doc.close()
