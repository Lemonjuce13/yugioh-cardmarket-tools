"""High-level orchestration: turn a list of orders into final PDF bytes.

Handles the start-position offset (skip already-used stickers), pagination across multiple A4
sheets, and overlaying the franking labels after the text base is drawn.
"""

from __future__ import annotations

from . import label, render
from .config import DEFAULT_SENDER
from .layouts import DEFAULT, LayoutSpec
from .models import Order
from .sheets import AMAZON_A4_4UP, SheetSpec


def assign_slots(order_count: int, capacity: int, start_position: int) -> list[dict[int, int]]:
    """Map orders to (page, slot) honoring a 1-based ``start_position`` on the first page.

    Returns a list of pages; each page maps slot_index -> order_index. Useful standalone for
    geometry tests.
    """
    if not 1 <= start_position <= capacity:
        raise ValueError(f"start_position must be 1..{capacity}, got {start_position}")
    pages: list[dict[int, int]] = []
    slot = start_position - 1
    page: dict[int, int] = {}
    for order_index in range(order_count):
        if slot >= capacity:
            pages.append(page)
            page = {}
            slot = 0
        page[slot] = order_index
        slot += 1
    if page or not pages:
        pages.append(page)
    return pages


def build_pdf(
    orders: list[Order],
    sheet: SheetSpec = AMAZON_A4_4UP,
    layout: LayoutSpec = DEFAULT,
    sender_lines: list[str] | None = None,
    start_position: int = 1,
) -> bytes:
    """Render ``orders`` onto one or more sheets and return print-ready PDF bytes."""
    sender_lines = sender_lines if sender_lines is not None else list(DEFAULT_SENDER)
    slot_pages = assign_slots(len(orders), sheet.capacity, start_position)

    # pages of slot_index -> Order, for the text renderer
    order_pages: list[dict[int, Order]] = [
        {slot: orders[oi] for slot, oi in page.items()} for page in slot_pages
    ]
    pdf_bytes = render.draw_pdf(order_pages, sheet, layout, sender_lines)

    # collect franking-label placements (absolute mm rects) for the ones that have a label
    placements: list[label.Placement] = []
    for page_index, page in enumerate(order_pages):
        for slot, order in page.items():
            if order.tracking_label is not None:
                zone = layout.zones(sheet.content_rect(slot))["label"]
                placements.append((page_index, zone, order.tracking_label))

    return label.embed_labels(pdf_bytes, placements)


def build_calibration_pdf(sheet: SheetSpec = AMAZON_A4_4UP) -> bytes:
    """Convenience wrapper for the calibration sheet."""
    return render.draw_calibration_sheet(sheet)
