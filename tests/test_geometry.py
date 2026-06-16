"""Geometry, slot-assignment and end-to-end PDF smoke tests (no sample files needed)."""

from __future__ import annotations

import pytest

from yugioh_shipping.core.layouts import DEFAULT
from yugioh_shipping.core.models import Address, Order
from yugioh_shipping.core.pipeline import assign_slots, build_calibration_pdf, build_pdf
from yugioh_shipping.core.preview import page_count
from yugioh_shipping.core.sheets import AMAZON_A4_4UP as S


def test_sticker_rects_stack_vertically():
    assert (S.sticker_rect(0).x, S.sticker_rect(0).y) == (8.5, 25.0)
    assert S.sticker_rect(0).w == 193.0 and S.sticker_rect(0).h == 60.0
    assert S.sticker_rect(1).y == 85.0
    assert S.sticker_rect(3).y == 205.0


def test_sticker_rect_out_of_range():
    with pytest.raises(IndexError):
        S.sticker_rect(S.capacity)


def test_content_rect_is_padded():
    c = S.content_rect(0)
    assert c.x == 8.5 + S.inner_pad
    assert c.w == 193.0 - 2 * S.inner_pad


def test_zones_are_ordered_left_to_right():
    z = DEFAULT.zones(S.content_rect(0))
    assert z["sender"].right <= z["label"].x
    assert z["label"].right <= z["recipient"].x
    assert z["recipient"].w > 0


def test_assign_slots_fills_and_paginates():
    assert assign_slots(6, 4, 1) == [{0: 0, 1: 1, 2: 2, 3: 3}, {0: 4, 1: 5}]


def test_assign_slots_honors_start_offset():
    # start at position 3 -> first two slots blank on page 1
    pages = assign_slots(6, 4, 3)
    assert pages[0] == {2: 0, 3: 1}
    assert pages[1] == {0: 2, 1: 3, 2: 4, 3: 5}


def test_assign_slots_rejects_bad_start():
    with pytest.raises(ValueError):
        assign_slots(1, 4, 0)
    with pytest.raises(ValueError):
        assign_slots(1, 4, 5)


def _order(name: str) -> Order:
    return Order(recipient=Address(lines=[name, "Teststr. 1", "12345 Berlin", "Germany"]))


def test_build_pdf_smoke_single_page():
    pdf = build_pdf([_order("Max Mustermann")], start_position=3)
    assert pdf[:4] == b"%PDF"
    assert page_count(pdf) == 1


def test_build_pdf_paginates_to_second_sheet():
    pdf = build_pdf([_order(f"Buyer {i}") for i in range(6)])
    assert page_count(pdf) == 2


def test_porto_does_not_crash_and_uppercases_in_pdf():
    pdf = build_pdf([Order(recipient=Address(["A", "B", "12345 C", "Germany"]), porto_code="cvnkp8vn")])
    assert pdf[:4] == b"%PDF"


def test_calibration_sheet():
    pdf = build_calibration_pdf()
    assert pdf[:4] == b"%PDF"
    assert page_count(pdf) == 1
