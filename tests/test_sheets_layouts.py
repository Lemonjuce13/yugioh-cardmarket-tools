"""Sheet/layout registries and zone splitting."""

from __future__ import annotations

import pytest

from yugioh_shipping.core.layouts import DEFAULT, get_layout, list_layouts
from yugioh_shipping.core.sheets import AMAZON_A4_4UP as S
from yugioh_shipping.core.sheets import get_sheet, list_sheets


def test_get_sheet_ok():
    assert get_sheet("amazon_a4_4up") is S


def test_get_sheet_unknown_raises():
    with pytest.raises(KeyError):
        get_sheet("does-not-exist")


def test_list_sheets_contains_default():
    assert S in list_sheets()


def test_get_layout_ok_and_unknown():
    assert get_layout("default") is DEFAULT
    with pytest.raises(KeyError):
        get_layout("nope")


def test_list_layouts():
    assert DEFAULT in list_layouts()


def test_capacity_matches_grid():
    assert S.capacity == S.rows * S.cols == 4


def test_zones_widths_and_bounds():
    c = S.content_rect(0)
    z = DEFAULT.zones(c)
    assert z["sender"].w == pytest.approx(DEFAULT.sender_width)
    assert z["label"].w == pytest.approx(DEFAULT.label_width)
    assert z["recipient"].w > 0
    # zones stay inside the content rect and the recipient ends at its right edge
    assert z["sender"].x == pytest.approx(c.x)
    assert z["recipient"].right == pytest.approx(c.right)
    assert z["recipient"].right <= c.right + 1e-9


def test_all_stickers_within_printable_area():
    for i in range(S.capacity):
        r = S.sticker_rect(i)
        assert r.x >= S.margin_left - 1e-9
        assert r.right <= S.page_w - S.margin_right + 1e-9
        assert r.y >= S.margin_top - 1e-9
        assert r.bottom <= S.page_h - S.margin_bottom + 1e-6
