"""Batch input: build a list of Orders from a CSV or JSON manifest.

Each entry supplies a recipient (inline lines OR a path to a Cardmarket PDF) plus optional
``porto_code`` and ``tracking_label`` (path to the franking-label PDF). Relative paths are
resolved against the manifest's own directory.

JSON shape::

    [
      {"recipient_pdf": "envelope-123.pdf", "porto_code": "CVNKP8VN"},
      {"recipient": ["Max Mustermann", "Hauptstr. 1", "12345 Berlin", "Germany"],
       "tracking_label": "Briefmarken.123.pdf"}
    ]

CSV columns (header row required): ``recipient`` (lines separated by ``;`` or ``|``),
``recipient_pdf``, ``porto_code``, ``tracking_label``. Unused columns may be left empty.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from ..core.models import Address, Order
from . import cardmarket


def _resolve(base: Path, value: str | None) -> Path | None:
    if not value:
        return None
    p = Path(value)
    return p if p.is_absolute() else (base / p)


def _recipient_from(entry: dict, base: Path) -> Address:
    pdf = _resolve(base, entry.get("recipient_pdf"))
    if pdf:
        return cardmarket.auto_parse(pdf, name=pdf.name)
    recipient = entry.get("recipient")
    if isinstance(recipient, list):
        return Address(lines=[str(x).strip() for x in recipient if str(x).strip()])
    if isinstance(recipient, str) and recipient.strip():
        parts = recipient.replace("|", ";").replace("\n", ";").split(";")
        return Address(lines=[p.strip() for p in parts if p.strip()])
    raise ValueError(f"manifest entry has no recipient: {entry!r}")


def _entry_to_order(entry: dict, base: Path) -> Order:
    tracking = _resolve(base, entry.get("tracking_label"))
    porto = (entry.get("porto_code") or "").strip() or None
    return Order(
        recipient=_recipient_from(entry, base),
        porto_code=porto,
        tracking_label=tracking,
    )


def load_manifest(path: str | Path) -> list[Order]:
    path = Path(path)
    base = path.parent
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("JSON manifest must be a list of order objects")
        entries = data
    elif path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8", newline="") as fh:
            entries = list(csv.DictReader(fh))
    else:
        raise ValueError(f"unsupported manifest type '{path.suffix}' (use .json or .csv)")

    return [_entry_to_order(e, base) for e in entries]
