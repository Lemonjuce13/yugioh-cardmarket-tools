"""Locate the optional real sample files (in asset/, with a project-root fallback).

Imported by tests so sample-dependent cases can ``skipif`` cleanly when the files are absent.
"""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_DIRS = [_ROOT / "asset", _ROOT]


def first(glob: str) -> Path | None:
    for base in _DIRS:
        matches = sorted(base.glob(glob))
        if matches:
            return matches[0]
    return None


ENVELOPE = first("envelope-*.pdf")
SALE = first("Sale_*.pdf")
LABEL = first("Briefmarken*.pdf")
