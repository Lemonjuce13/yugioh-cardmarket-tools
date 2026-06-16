"""Extract the recipient address from the two Cardmarket export PDFs.

- ``envelope-<id>-*.pdf`` : print-envelope layout. The recipient is the **largest-font** text
  block (the small sender line on top is ignored).
- ``Sale_#<id>.pdf``      : full sale detail. The recipient follows the ``Buyer`` anchor; the
  ``Shipping Method`` is read as a hint.

Both PDFs have a real text layer, so no OCR is needed.
"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF

from ..core.models import Address

_STOP_PREFIXES = ("unpaid:", "paid:", "contents", "seller", "buyer", "not yet", "article", "shipping")
_COUNTRY_WORDS = {"germany", "deutschland"}


def _open(src: bytes | str | Path) -> fitz.Document:
    if isinstance(src, (bytes, bytearray)):
        return fitz.open(stream=bytes(src), filetype="pdf")
    return fitz.open(str(src))


def parse_envelope_pdf(src: bytes | str | Path) -> Address:
    """Recipient = the lines rendered in the largest font on page 1."""
    doc = _open(src)
    try:
        page = doc[0]
        lines: list[tuple[float, float, str]] = []  # (font_size, y, text)
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                text = "".join(s["text"] for s in spans).strip()
                if not text:
                    continue
                size = max((s["size"] for s in spans), default=0.0)
                lines.append((size, line["bbox"][1], text))
        if not lines:
            raise ValueError("no text found in envelope PDF")
        max_size = max(s for s, _, _ in lines)
        recipient = sorted(
            ((y, t) for s, y, t in lines if s >= max_size - 0.5), key=lambda it: it[0]
        )
        return Address(lines=[t for _, t in recipient])
    finally:
        doc.close()


def parse_sale_pdf(src: bytes | str | Path) -> tuple[Address, str | None]:
    """Recipient from the ``Buyer`` block; also returns the shipping method if present."""
    doc = _open(src)
    try:
        raw = [ln.strip() for ln in doc[0].get_text("text").splitlines()]
    finally:
        doc.close()
    lines = [ln for ln in raw]

    # shipping method (label may share a line with its value, or be on the next line)
    shipping: str | None = None
    for i, ln in enumerate(lines):
        if ln.lower().startswith("shipping method"):
            rest = ln[len("shipping method"):].strip(" :\t")
            if rest:
                shipping = rest
            else:
                for nxt in lines[i + 1:]:
                    if nxt:
                        shipping = nxt
                        break
            break

    # buyer block: lines after the "Buyer" anchor until a country word or a stop keyword
    buyer_idx = next((i for i, ln in enumerate(lines) if ln.lower().startswith("buyer")), None)
    if buyer_idx is None:
        raise ValueError("no 'Buyer' section found in sale PDF")

    block: list[str] = []
    for ln in lines[buyer_idx + 1:]:
        if not ln:
            continue
        low = ln.lower()
        if any(low.startswith(p) for p in _STOP_PREFIXES) or "unpaid:" in low or "not yet" in low:
            break
        block.append(ln)
        if low in _COUNTRY_WORDS or low.endswith(("germany", "deutschland")):
            break

    if not block:
        raise ValueError("could not extract buyer address from sale PDF")
    return Address(lines=block), shipping


def auto_parse(src: bytes | str | Path, name: str | None = None) -> Address:
    """Pick the right parser by filename, then by content sniffing."""
    hint = (name or (str(src) if isinstance(src, (str, Path)) else "")).lower()
    if "envelope" in hint:
        return parse_envelope_pdf(src)
    if "sale" in hint:
        return parse_sale_pdf(src)[0]

    doc = _open(src)
    try:
        text = doc[0].get_text("text").lower()
    finally:
        doc.close()
    if "buyer" in text and "seller" in text:
        return parse_sale_pdf(src)[0]
    return parse_envelope_pdf(src)
