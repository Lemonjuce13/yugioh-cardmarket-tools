"""Geometry, slot-assignment and end-to-end PDF smoke tests (no sample files needed)."""

from __future__ import annotations

import fitz
import pytest

from postik.core.layouts import DEFAULT
from postik.core.models import Address, Order, normalize_porto_code
from postik.core.pipeline import assign_slots, build_calibration_pdf, build_pdf
from postik.core.preview import page_count
from postik.core.sheets import AMAZON_A4_4UP as S


def test_sticker_rects_stack_vertically():
    # relative to the (calibratable) SheetSpec, so tuning the constants never breaks tests
    r0 = S.sticker_rect(0)
    assert (r0.x, r0.y) == (S.margin_left, S.margin_top)
    assert (r0.w, r0.h) == (S.sticker_w, S.sticker_h)
    assert S.sticker_rect(1).y == S.margin_top + S.pitch_y
    assert S.sticker_rect(3).y == S.margin_top + 3 * S.pitch_y
    # the last sticker must not spill past the printable area
    assert S.sticker_rect(S.capacity - 1).bottom <= S.page_h - S.margin_bottom + 1e-6


def test_sticker_rect_out_of_range():
    with pytest.raises(IndexError):
        S.sticker_rect(S.capacity)


def test_content_rect_is_padded():
    c = S.content_rect(0)
    assert c.x == S.margin_left + S.inner_pad
    assert c.w == S.sticker_w - 2 * S.inner_pad


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


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("CVNKP8VN", "CVNKP8VN"),
        ("cvnkp8vn", "CVNKP8VN"),
        ("#PORTO\nCVNKP8VN", "CVNKP8VN"),  # the pasted DHL block
        ("#PORTO CVNKP8VN", "CVNKP8VN"),
        ("  #porto \r\n cvnkp8vn ", "CVNKP8VN"),
        ("#PORTO", None),
        ("", None),
        (None, None),
    ],
)
def test_normalize_porto_code(raw, expected):
    assert normalize_porto_code(raw) == expected


def _pdf_text(pdf: bytes) -> str:
    doc = fitz.open(stream=pdf, filetype="pdf")
    try:
        return "\n".join(page.get_text() for page in doc)
    finally:
        doc.close()


def test_pasted_porto_block_is_not_doubled():
    pdf = build_pdf([Order(recipient=Address(["A", "B", "12345 C", "Germany"]), porto_code="#PORTO\nCVNKP8VN")])
    text = _pdf_text(pdf)
    assert text.count("#PORTO") == 1
    assert text.count("CVNKP8VN") == 1


def test_calibration_sheet():
    pdf = build_calibration_pdf()
    assert pdf[:4] == b"%PDF"
    assert page_count(pdf) == 1
