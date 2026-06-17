"""Crop the Deutsche Post franking label out of its source PDF and embed it (vector, crisp)
into the blank label slot of the base sheet, using PyMuPDF.

Vector embedding via ``show_pdf_page(clip=...)`` keeps the DataMatrix sharp so it stays
scannable -- rasterizing it would risk an unreadable code.
"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF

from .sheets import Rect

PT_PER_MM = 72.0 / 25.4


def _open(src: bytes | str | Path) -> fitz.Document:
    if isinstance(src, (bytes, bytearray)):
        return fitz.open(stream=bytes(src), filetype="pdf")
    return fitz.open(str(src))


def detect_label_bbox(doc: fitz.Document, page: int = 0, margin_mm: float = 2.0) -> fitz.Rect:
    """Union of all text/vector/image content on ``page`` (+ a small margin), clamped to the
    page. This isolates the franking label from the surrounding empty A4 + crop marks.

    If a particular label PDF has stray full-page marks, pass an explicit ``crop_override`` to
    :func:`embed_labels` instead.
    """
    p = doc[page]
    rects: list[fitz.Rect] = []

    for block in p.get_text("dict")["blocks"]:
        bbox = block.get("bbox")
        if bbox:
            rects.append(fitz.Rect(bbox))
    for drawing in p.get_drawings():
        rects.append(fitz.Rect(drawing["rect"]))
    for img in p.get_images(full=True):
        try:
            rects.extend(fitz.Rect(r) for r in p.get_image_rects(img[0]))
        except Exception:
            pass

    rects = [r for r in rects if r.is_valid and not r.is_empty]
    if not rects:
        return p.rect

    bbox = +rects[0]
    for r in rects[1:]:
        bbox |= r
    m = margin_mm * PT_PER_MM
    bbox = fitz.Rect(bbox.x0 - m, bbox.y0 - m, bbox.x1 + m, bbox.y1 + m)
    bbox &= p.rect
    return bbox


def _aspect_fit(clip: fitz.Rect, target: fitz.Rect) -> fitz.Rect:
    """Largest sub-rect of ``target`` with ``clip``'s aspect ratio, centred -- avoids distortion."""
    cw, ch, tw, th = clip.width, clip.height, target.width, target.height
    if cw <= 0 or ch <= 0 or tw <= 0 or th <= 0:
        return target
    scale = min(tw / cw, th / ch)
    w, h = cw * scale, ch * scale
    x0 = target.x0 + (tw - w) / 2
    y0 = target.y0 + (th - h) / 2
    return fitz.Rect(x0, y0, x0 + w, y0 + h)


# A placement = (page_index, label_zone_rect_in_mm, label_source)
Placement = tuple[int, Rect, "bytes | str | Path"]


def embed_labels(
    pdf_bytes: bytes,
    placements: list[Placement],
    label_page: int = 0,
    crop_override: tuple[float, float, float, float] | None = None,
) -> bytes:
    """Overlay each franking label into its slot on the base PDF. Returns new PDF bytes."""
    if not placements:
        return pdf_bytes

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        for page_index, zone, src in placements:
            label_doc = _open(src)
            try:
                clip = fitz.Rect(*crop_override) if crop_override else detect_label_bbox(label_doc, label_page)
                target = fitz.Rect(
                    zone.x * PT_PER_MM,
                    zone.y * PT_PER_MM,
                    zone.right * PT_PER_MM,
                    zone.bottom * PT_PER_MM,
                )
                fit = _aspect_fit(clip, target)
                doc[page_index].show_pdf_page(fit, label_doc, label_page, clip=clip)
            finally:
                label_doc.close()
        return doc.tobytes()
    finally:
        doc.close()
