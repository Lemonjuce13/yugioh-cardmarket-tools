"""Rendering internals + end-to-end PDF properties (page size, pagination, shrink-to-fit)."""

from __future__ import annotations

import fitz

from postik.core.models import Address, Order
from postik.core.pipeline import build_pdf
from postik.core.preview import page_count
from postik.core.render import _fit_font_size
from postik.core.sheets import AMAZON_A4_4UP as S

PT = 72.0 / 25.4


def _order(name: str) -> Order:
    return Order(Address([name, "Teststr. 1", "12345 Berlin", "Germany"]))


def test_fit_font_size_shrinks_for_long_text():
    assert _fit_font_size(["X" * 80], "Helvetica", 12, max_w=50, max_h=500, spacing=1.18) < 12


def test_fit_font_size_keeps_when_it_fits():
    assert _fit_font_size(["short"], "Helvetica", 12, max_w=500, max_h=500, spacing=1.18) == 12


def test_fit_font_size_respects_min_bound():
    assert _fit_font_size(["X" * 999], "Helvetica", 12, max_w=5, max_h=5, spacing=1.18) >= 6


def test_page_is_a4_sized():
    pdf = build_pdf([_order("Max")])
    doc = fitz.open(stream=pdf, filetype="pdf")
    r = doc[0].rect
    assert abs(r.width - S.page_w * PT) < 1.0
    assert abs(r.height - S.page_h * PT) < 1.0


def test_three_pages_with_offset():
    pdf = build_pdf([_order(f"Buyer {i}") for i in range(9)], start_position=3)
    assert page_count(pdf) == 3


def test_empty_orders_yields_one_blank_page():
    pdf = build_pdf([])
    assert pdf[:4] == b"%PDF"
    assert page_count(pdf) == 1


def test_very_long_recipient_does_not_crash():
    long_name = "A really really long recipient line that must be shrunk down to fit the zone"
    pdf = build_pdf([Order(Address([long_name, "Str 1", "12345 City", "Germany"]))])
    assert pdf[:4] == b"%PDF"


def test_recipient_and_sender_text_present():
    pdf = build_pdf([_order("Maximilian")], sender_lines=["MySender GmbH", "Weg 1", "1 City"])
    text = "\n".join(p.get_text() for p in fitz.open(stream=pdf, filetype="pdf"))
    assert "Maximilian" in text
    assert "MySender GmbH" in text
