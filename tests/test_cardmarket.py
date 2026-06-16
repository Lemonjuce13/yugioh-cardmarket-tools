"""Parse the real Cardmarket sample PDFs shipped in the project root.

These tests skip automatically if the sample files are not present.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from yugioh_shipping.core.models import Order
from yugioh_shipping.core.pipeline import build_pdf
from yugioh_shipping.core.preview import page_count
from yugioh_shipping.io import cardmarket

ROOT = Path(__file__).resolve().parents[1]
# samples live in asset/ (with a fallback to the project root)
SAMPLE_DIRS = [ROOT / "asset", ROOT]


def _first(glob: str) -> Path | None:
    for base in SAMPLE_DIRS:
        matches = sorted(base.glob(glob))
        if matches:
            return matches[0]
    return None


ENVELOPE = _first("envelope-*.pdf")
SALE = _first("Sale_*.pdf")
LABEL = _first("Briefmarken*.pdf")


@pytest.mark.skipif(ENVELOPE is None, reason="no envelope-*.pdf sample present")
def test_parse_envelope_recipient():
    addr = cardmarket.parse_envelope_pdf(ENVELOPE)
    joined = " ".join(addr.lines)
    assert "Maximilian Eßer" in joined
    assert "Buchenstraße 35" in joined
    assert "50354 Hürth Gleuel" in joined
    # the small sender line must NOT be picked up as the recipient
    assert not any("Flottmoorpark" in ln for ln in addr.lines)


@pytest.mark.skipif(SALE is None, reason="no Sale_*.pdf sample present")
def test_parse_sale_buyer_and_shipping():
    addr, shipping = cardmarket.parse_sale_pdf(SALE)
    joined = " ".join(addr.lines)
    assert "Maximilian Eßer" in joined
    assert "Hürth Gleuel" in joined
    assert "Gerrit Schelling" not in joined  # that's the seller
    assert shipping == "Standardbrief"


@pytest.mark.skipif(ENVELOPE is None, reason="no envelope-*.pdf sample present")
def test_auto_parse_by_filename():
    addr = cardmarket.auto_parse(ENVELOPE, name=ENVELOPE.name)
    assert "Maximilian Eßer" in " ".join(addr.lines)


@pytest.mark.skipif(ENVELOPE is None or LABEL is None, reason="need envelope + label samples")
def test_build_pdf_with_embedded_franking_label():
    addr = cardmarket.parse_envelope_pdf(ENVELOPE)
    pdf = build_pdf([Order(recipient=addr, porto_code="CVNKP8VN", tracking_label=LABEL)])
    assert pdf[:4] == b"%PDF"
    assert page_count(pdf) == 1
