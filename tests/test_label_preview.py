"""Franking-label crop/embed (PyMuPDF) and PNG preview."""

from __future__ import annotations

import fitz
import pytest

from samples import LABEL

from yugioh_shipping.core.label import _aspect_fit, detect_label_bbox, embed_labels
from yugioh_shipping.core.layouts import DEFAULT
from yugioh_shipping.core.models import Address, Order
from yugioh_shipping.core.pipeline import build_pdf
from yugioh_shipping.core.preview import page_count, render_page
from yugioh_shipping.core.sheets import AMAZON_A4_4UP as S

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _base() -> bytes:
    return build_pdf([Order(Address(["A", "Str 1", "12345 City", "Germany"]))])


def test_aspect_fit_preserves_ratio_and_centers():
    fit = _aspect_fit(fitz.Rect(0, 0, 100, 50), fitz.Rect(0, 0, 100, 100))  # 2:1 into a square
    assert fit.width / fit.height == pytest.approx(2.0)
    assert fit.x0 == pytest.approx(0.0)
    assert fit.y0 == pytest.approx(25.0)  # vertically centred
    assert fit.x1 <= 100 + 1e-6 and fit.y1 <= 100 + 1e-6


def test_aspect_fit_degenerate_clip_returns_target():
    target = fitz.Rect(0, 0, 10, 10)
    assert _aspect_fit(fitz.Rect(0, 0, 0, 0), target) == target


def test_preview_returns_png():
    assert render_page(_base())[:8] == PNG_MAGIC


def test_preview_dpi_scales_size():
    pdf = _base()
    assert len(render_page(pdf, dpi=200)) > len(render_page(pdf, dpi=72))


def test_embed_no_placements_is_noop():
    base = _base()
    assert embed_labels(base, []) is base


@pytest.mark.skipif(LABEL is None, reason="no Briefmarken*.pdf sample present")
def test_detect_label_bbox_is_subregion_of_page():
    doc = fitz.open(LABEL)
    bbox = detect_label_bbox(doc)
    page = doc[0].rect
    assert 0 < bbox.width < page.width
    assert 0 < bbox.height < page.height
    assert bbox.x0 >= page.x0 - 1 and bbox.y0 >= page.y0 - 1
    assert bbox.x1 <= page.x1 + 1 and bbox.y1 <= page.y1 + 1


@pytest.mark.skipif(LABEL is None, reason="no Briefmarken*.pdf sample present")
def test_embed_label_with_auto_and_override_crop():
    zone = DEFAULT.zones(S.content_rect(0))["label"]
    auto = embed_labels(_base(), [(0, zone, LABEL)])
    override = embed_labels(_base(), [(0, zone, LABEL)], crop_override=(40, 40, 220, 150))
    for out in (auto, override):
        assert out[:4] == b"%PDF"
        assert page_count(out) == 1
