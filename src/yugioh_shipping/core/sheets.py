"""Sticker-sheet geometry.

Everything physical lives here as *data* (a :class:`SheetSpec`) so calibrating after a test
print is just editing numbers, and supporting a different sticker sheet later is just adding
another :class:`SheetSpec` to the registry -- no code changes.

Coordinate convention: all rectangles use a **top-left origin in millimetres** (x to the
right, y downward), which matches how the sheet is measured with a ruler. The renderer
converts to ReportLab's bottom-left points; PyMuPDF already uses top-left points.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rect:
    """A rectangle in millimetres, top-left origin."""

    x: float
    y: float
    w: float
    h: float

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h


@dataclass(frozen=True)
class SheetSpec:
    """Describes one printable sticker sheet.

    A sheet is a regular grid of ``rows`` x ``cols`` stickers. ``pitch_y`` / ``pitch_x`` are
    the top-to-top / left-to-left distances between adjacent stickers (which differ from the
    sticker size when there are gaps between die-cuts). Tune ``margin_*`` and ``pitch_*`` with
    the calibration sheet after the first test print.
    """

    id: str
    name: str
    page_w: float
    page_h: float
    margin_top: float
    margin_bottom: float
    margin_left: float
    margin_right: float
    rows: int
    cols: int
    sticker_w: float
    sticker_h: float
    pitch_y: float
    pitch_x: float = 0.0
    inner_pad: float = 4.0  # keep content this far inside each sticker edge

    @property
    def capacity(self) -> int:
        """Number of stickers per sheet."""
        return self.rows * self.cols

    def sticker_rect(self, index: int) -> Rect:
        """Outer rectangle of sticker ``index`` (0-based, row-major: top→bottom, left→right)."""
        if not 0 <= index < self.capacity:
            raise IndexError(f"sticker index {index} out of range 0..{self.capacity - 1}")
        row, col = divmod(index, self.cols)
        pitch_x = self.pitch_x or self.sticker_w
        x = self.margin_left + col * pitch_x
        y = self.margin_top + row * self.pitch_y
        return Rect(x, y, self.sticker_w, self.sticker_h)

    def content_rect(self, index: int) -> Rect:
        """Inner (padded) rectangle of sticker ``index`` -- where content may be drawn."""
        r = self.sticker_rect(index)
        p = self.inner_pad
        return Rect(r.x + p, r.y + p, r.w - 2 * p, r.h - 2 * p)


# --- Registry ---------------------------------------------------------------------------

# Amazon A4 sheet: 4 large labels stacked vertically. Measurements are approximate; calibrate.
AMAZON_A4_4UP = SheetSpec(
    id="amazon_a4_4up",
    name="Amazon A4 - 4 large labels (vertical)",
    page_w=210.0,
    page_h=297.0,
    margin_top=26.5,
    margin_bottom=26.5,
    margin_left=9.0,
    margin_right=9.0,
    rows=4,
    cols=1,
    sticker_w=192.0,
    sticker_h=61.0,
    pitch_y=61.0,  # raise toward ~61.75 if the labels have gaps between them (calibrate!)
    pitch_x=0.0,
    inner_pad=4.0,
)

SHEETS: dict[str, SheetSpec] = {AMAZON_A4_4UP.id: AMAZON_A4_4UP}
DEFAULT_SHEET_ID = AMAZON_A4_4UP.id


def get_sheet(sheet_id: str) -> SheetSpec:
    try:
        return SHEETS[sheet_id]
    except KeyError:
        raise KeyError(f"unknown sheet '{sheet_id}'. Available: {', '.join(SHEETS)}") from None


def list_sheets() -> list[SheetSpec]:
    return list(SHEETS.values())
