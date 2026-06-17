"""CSV/JSON manifest loading."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from samples import ENVELOPE

from postik.io.manifest import load_manifest


def test_json_inline_list_and_string(tmp_path):
    p = tmp_path / "m.json"
    p.write_text(
        json.dumps(
            [
                {"recipient": ["Max", "Str 1", "12345 Berlin", "Germany"], "porto_code": "#PORTO CVNKP8VN"},
                {"recipient": "Anna; Weg 2; 54321 Köln; Germany"},
            ]
        ),
        encoding="utf-8",
    )
    orders = load_manifest(p)
    assert len(orders) == 2
    assert orders[0].recipient.lines[0] == "Max"
    assert orders[0].porto_code == "CVNKP8VN"  # marker stripped + uppercased
    assert orders[1].recipient.lines == ["Anna", "Weg 2", "54321 Köln", "Germany"]


def test_csv_with_quoted_recipient(tmp_path):
    p = tmp_path / "m.csv"
    p.write_text(
        'recipient,porto_code\n"Max;Str 1;12345 Berlin;Germany",cvnkp8vn\n',
        encoding="utf-8",
    )
    orders = load_manifest(p)
    assert len(orders) == 1
    assert orders[0].recipient.lines[0] == "Max"
    assert orders[0].porto_code == "CVNKP8VN"


def test_tracking_path_resolved_relative_to_manifest(tmp_path):
    (tmp_path / "label.pdf").write_bytes(b"%PDF-1.4 dummy")
    p = tmp_path / "m.json"
    p.write_text(json.dumps([{"recipient": ["A"], "tracking_label": "label.pdf"}]), encoding="utf-8")
    order = load_manifest(p)[0]
    assert order.tracking_label == tmp_path / "label.pdf"


def test_missing_recipient_raises(tmp_path):
    p = tmp_path / "m.json"
    p.write_text(json.dumps([{"porto_code": "X"}]), encoding="utf-8")
    with pytest.raises(ValueError):
        load_manifest(p)


def test_unsupported_extension_raises(tmp_path):
    p = tmp_path / "m.txt"
    p.write_text("nope", encoding="utf-8")
    with pytest.raises(ValueError):
        load_manifest(p)


def test_json_must_be_a_list(tmp_path):
    p = tmp_path / "m.json"
    p.write_text(json.dumps({"recipient": ["A"]}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_manifest(p)


@pytest.mark.skipif(ENVELOPE is None, reason="no envelope-*.pdf sample present")
def test_recipient_pdf_reference(tmp_path):
    p = tmp_path / "m.json"
    p.write_text(json.dumps([{"recipient_pdf": str(ENVELOPE)}]), encoding="utf-8")
    order = load_manifest(p)[0]
    assert any("Eßer" in ln for ln in order.recipient.lines)
