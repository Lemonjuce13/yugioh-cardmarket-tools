"""ReportLab rendering of the base sticker sheet (text only) and the calibration sheet.

The franking label slot is intentionally left blank here; it is filled afterwards by
:mod:`postik.core.label` (PyMuPDF) so the DataMatrix stays crisp/vector.

All public functions return PDF ``bytes`` so every frontend can consume them without touching
the filesystem.
"""

from __future__ import annotations

import io

from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from .layouts import LayoutSpec
from .models import Order, normalize_porto_code
from .sheets import Rect, SheetSpec


def _rl_rect(rect: Rect, sheet: SheetSpec) -> tuple[float, float, float, float]:
    """Convert a top-left mm Rect to ReportLab points with bottom-left origin: (x, y, w, h)."""
    x = rect.x * mm
    y = (sheet.page_h - rect.bottom) * mm
    return x, y, rect.w * mm, rect.h * mm


def _fit_font_size(
    lines: list[str], font: str, size: float, max_w: float, max_h: float, spacing: float, min_size: float = 6.0
) -> float:
    """Shrink ``size`` (points) until ``lines`` fit within ``max_w`` x ``max_h`` (points)."""
    s = size
    while s > min_size:
        widest = max((stringWidth(ln, font, s) for ln in lines), default=0.0)
        total_h = len(lines) * s * spacing
        if widest <= max_w and total_h <= max_h:
            break
        s -= 0.5
    return s


def _draw_block_top(
    c: canvas.Canvas, lines: list[str], rect_pt: tuple[float, float, float, float], font: str, size: float, spacing: float
) -> None:
    """Draw text lines top-aligned within a points rect (bottom-left origin)."""
    x, y, _w, h = rect_pt
    leading = size * spacing
    baseline = y + h - size  # first line's baseline near the top
    c.setFont(font, size)
    for line in lines:
        c.drawString(x, baseline, line)
        baseline -= leading


def _draw_porto(c: canvas.Canvas, code: str, rect_pt: tuple[float, float, float, float], font: str, size: float, spacing: float) -> float:
    """Draw the two-line #PORTO block at the bottom of ``rect_pt``. Returns its top (points).

    CRITICAL: literal '#PORTO' (upper) on its own line, the code (upper) on the next line, same
    font size, never concatenated -- the post-office scanner requires this two-line form.
    """
    x, y, _w, _h = rect_pt
    leading = size * spacing
    margin = 1.0 * mm
    code_baseline = y + margin
    porto_baseline = code_baseline + leading
    c.setFont(font, size)
    c.drawString(x, porto_baseline, "#PORTO")
    c.drawString(x, code_baseline, normalize_porto_code(code) or "")
    return porto_baseline + size  # approx top of the block


def _draw_sticker(c: canvas.Canvas, slot_index: int, order: Order, sheet: SheetSpec, layout: LayoutSpec, sender_lines: list[str]) -> None:
    content = sheet.content_rect(slot_index)
    zones = layout.zones(content)

    # Sender (left, small)
    _draw_block_top(c, sender_lines, _rl_rect(zones["sender"], sheet), layout.font_name, layout.sender_font_size, layout.line_spacing)

    # Recipient (right, large) -- reserve space at the bottom for #PORTO if present.
    rx, ry, rw, rh = _rl_rect(zones["recipient"], sheet)
    porto_reserve = 0.0
    if order.porto_code:
        porto_reserve = (2 * layout.porto_font_size * layout.line_spacing) + layout.porto_gap * mm
    avail_h = max(0.0, rh - porto_reserve)
    rec_lines = order.recipient.lines or [""]
    size = _fit_font_size(rec_lines, layout.font_name, layout.recipient_font_size, rw, avail_h, layout.line_spacing)
    # draw recipient in the top part of the zone (above the porto reserve)
    _draw_block_top(c, rec_lines, (rx, ry + porto_reserve, rw, avail_h), layout.font_name, size, layout.line_spacing)

    # #PORTO block at the bottom of the recipient zone
    if order.porto_code:
        _draw_porto(c, order.porto_code, (rx, ry, rw, rh), layout.font_name, layout.porto_font_size, layout.line_spacing)

    # Label slot is left blank here -- embedded later by label.embed_labels().


def draw_pdf(pages: list[dict[int, Order]], sheet: SheetSpec, layout: LayoutSpec, sender_lines: list[str]) -> bytes:
    """Render the multi-page base sheet. ``pages[i]`` maps slot_index -> Order for page ``i``."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(sheet.page_w * mm, sheet.page_h * mm))
    if not pages:
        pages = [{}]
    for page in pages:
        for slot_index, order in sorted(page.items()):
            _draw_sticker(c, slot_index, order, sheet, layout, sender_lines)
        c.showPage()
    c.save()
    return buf.getvalue()


def draw_calibration_sheet(sheet: SheetSpec) -> bytes:
    """A single page outlining every sticker + corner crosshairs + a mm ruler, for tuning."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(sheet.page_w * mm, sheet.page_h * mm))

    c.setLineWidth(0.3)
    for i in range(sheet.capacity):
        r = sheet.sticker_rect(i)
        x, y, w, h = _rl_rect(r, sheet)
        c.rect(x, y, w, h)
        # corner crosshairs
        for cx, cy in ((x, y), (x + w, y), (x, y + h), (x + w, y + h)):
            c.line(cx - 3 * mm, cy, cx + 3 * mm, cy)
            c.line(cx, cy - 3 * mm, cx, cy + 3 * mm)
        # label inside each sticker
        c.setFont("Helvetica", 7)
        c.drawString(x + 2 * mm, y + h - 9, f"sticker {i + 1}  ({r.w:.0f}x{r.h:.0f} mm)")

    # top ruler (every 10 mm) along the printable left margin reference
    c.setFont("Helvetica", 5)
    for mm_x in range(0, int(sheet.page_w) + 1, 10):
        px = mm_x * mm
        c.line(px, sheet.page_h * mm, px, sheet.page_h * mm - 4 * mm)
        c.drawString(px + 0.5 * mm, sheet.page_h * mm - 6 * mm, str(mm_x))
    for mm_y in range(0, int(sheet.page_h) + 1, 10):
        py = (sheet.page_h - mm_y) * mm
        c.line(0, py, 4 * mm, py)
        c.drawString(4.5 * mm, py - 1.5, str(mm_y))

    c.showPage()
    c.save()
    return buf.getvalue()
