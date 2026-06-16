"""Address parsing and porto-code normalization."""

from __future__ import annotations

import pytest

from yugioh_shipping.core.models import Address, normalize_porto_code


def test_address_from_text_strips_and_drops_blanks():
    a = Address.from_text("  Max \r\n\n Buchenstraße 35 \n\n50354 Hürth\n")
    assert a.lines == ["Max", "Buchenstraße 35", "50354 Hürth"]


def test_address_bool():
    assert not Address([])
    assert not Address.from_text("   \n  ")
    assert Address(["x"])


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("CVNKP8VN", "CVNKP8VN"),
        ("cvnkp8vn", "CVNKP8VN"),
        ("#PORTO\nCVNKP8VN", "CVNKP8VN"),
        ("#PORTO CVNKP8VN", "CVNKP8VN"),
        ("  #porto \r\n cvnkp8vn ", "CVNKP8VN"),
        ("PORTO\nCVNKP8VN", "CVNKP8VN"),  # marker without the leading '#'
        ("#PORTO", None),
        ("   ", None),
        ("", None),
        (None, None),
    ],
)
def test_normalize_porto_code(raw, expected):
    assert normalize_porto_code(raw) == expected


def test_normalize_is_idempotent():
    once = normalize_porto_code("#PORTO CVNKP8VN")
    assert normalize_porto_code(once) == once == "CVNKP8VN"


def test_normalize_keeps_internal_spacing_minus_marker():
    assert normalize_porto_code("#PORTO AB CD") == "AB CD"
