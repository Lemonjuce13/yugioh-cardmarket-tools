"""Core data models shared by every frontend.

Kept deliberately free of any rendering / I/O concerns so the CLI, the FastAPI stub and a
future GUI all speak the same vocabulary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Address:
    """A postal address as a list of display lines (already in the order to print)."""

    lines: list[str] = field(default_factory=list)

    @classmethod
    def from_text(cls, text: str) -> "Address":
        """Parse a pasted/typed multi-line block into an Address (blank lines dropped)."""
        norm = text.replace("\r\n", "\n").replace("\r", "\n")
        cleaned = [ln.strip() for ln in norm.split("\n")]
        return cls(lines=[ln for ln in cleaned if ln])

    def __bool__(self) -> bool:
        return bool(self.lines)


@dataclass
class Order:
    """One shipment = one sticker.

    ``porto_code`` and ``tracking_label`` are independent optionals: a cheap order usually has
    a #PORTO code, a high-value order an Einschreiben franking label (which already includes
    postage). ``tracking_label`` may be raw PDF ``bytes`` (API upload) or a ``Path`` (CLI).
    """

    recipient: Address
    porto_code: str | None = None
    tracking_label: bytes | Path | None = None
    # optional metadata (useful for cross-referencing / future features)
    sale_id: str | None = None
    shipping_method: str | None = None
