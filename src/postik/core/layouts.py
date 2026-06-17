"""Block layout within a single sticker.

Like sheets, a layout is *data* (:class:`LayoutSpec`) so rearranging blocks or adding an
alternative arrangement later is an addition, not a rewrite. The default places:

    [ sender (small, left) ] [ franking label (middle) ] [ recipient (large, right) ]

with the #PORTO block anchored at the **bottom of the recipient (right) zone**.
"""

from __future__ import annotations

from dataclasses import dataclass

from .sheets import Rect


@dataclass(frozen=True)
class LayoutSpec:
    id: str
    name: str
    sender_width: float  # mm reserved for the sender zone (left)
    label_width: float  # mm reserved for the franking-label slot (middle)
    zone_gap: float = 3.0  # mm horizontal gap between zones
    font_name: str = "Helvetica"  # WinAnsi-encoded -> covers ä ö ü ß
    sender_font_size: float = 8.0
    recipient_font_size: float = 12.0
    porto_font_size: float = 12.0  # #PORTO line and the code share this size
    line_spacing: float = 1.18  # multiple of font size
    porto_gap: float = 2.0  # mm gap between recipient block and the #PORTO block

    def zones(self, content: Rect) -> dict[str, Rect]:
        """Split a sticker's content rect into sender / label / recipient zones (mm)."""
        sender = Rect(content.x, content.y, self.sender_width, content.h)
        lx = sender.right + self.zone_gap
        label = Rect(lx, content.y, self.label_width, content.h)
        rx = label.right + self.zone_gap
        recipient = Rect(rx, content.y, max(0.0, content.right - rx), content.h)
        return {"sender": sender, "label": label, "recipient": recipient}


DEFAULT = LayoutSpec(
    id="default",
    name="Sender left / label middle / recipient right",
    sender_width=58.0,
    label_width=55.0,
)

LAYOUTS: dict[str, LayoutSpec] = {DEFAULT.id: DEFAULT}
DEFAULT_LAYOUT_ID = DEFAULT.id


def get_layout(layout_id: str) -> LayoutSpec:
    try:
        return LAYOUTS[layout_id]
    except KeyError:
        raise KeyError(f"unknown layout '{layout_id}'. Available: {', '.join(LAYOUTS)}") from None


def list_layouts() -> list[LayoutSpec]:
    return list(LAYOUTS.values())
