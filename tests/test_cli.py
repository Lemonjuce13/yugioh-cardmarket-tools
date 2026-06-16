"""CLI entrypoint (non-interactive paths) via main(argv)."""

from __future__ import annotations

import json

import fitz
import pytest

from samples import ENVELOPE

from yugioh_shipping.cli.app import main

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _text(pdf_path) -> str:
    return "\n".join(p.get_text() for p in fitz.open(pdf_path))


def test_list_sheets(capsys):
    assert main(["--list-sheets"]) == 0
    out = capsys.readouterr().out
    assert "amazon_a4_4up" in out
    assert "default" in out


def test_calibration_writes_pdf(tmp_path):
    out = tmp_path / "cal.pdf"
    assert main(["--calibration", "-o", str(out)]) == 0
    assert out.read_bytes()[:4] == b"%PDF"


def test_inline_recipient_with_pasted_porto(tmp_path):
    out = tmp_path / "o.pdf"
    rc = main(["--recipient", "Max\\nStr 1\\n12345 Berlin\\nGermany", "--porto", "#PORTO CVNKP8VN", "-o", str(out)])
    assert rc == 0
    text = _text(out)
    assert text.count("#PORTO") == 1
    assert "CVNKP8VN" in text
    assert "Max" in text


def test_invalid_start_position_returns_2(tmp_path):
    out = tmp_path / "o.pdf"
    assert main(["--recipient", "A", "--start", "99", "-o", str(out)]) == 2
    assert not out.exists()


def test_preview_flag_writes_png(tmp_path):
    out = tmp_path / "o.pdf"
    png = tmp_path / "o.png"
    assert main(["--recipient", "A\\nB\\n12345 C\\nGermany", "-o", str(out), "--preview", str(png)]) == 0
    assert png.read_bytes()[:8] == PNG_MAGIC


def test_manifest_run(tmp_path):
    m = tmp_path / "m.json"
    m.write_text(
        json.dumps([{"recipient": ["Max", "Str 1", "12345 Berlin", "Germany"], "porto_code": "CVNKP8VN"}]),
        encoding="utf-8",
    )
    out = tmp_path / "o.pdf"
    assert main(["--manifest", str(m), "-o", str(out)]) == 0
    assert out.read_bytes()[:4] == b"%PDF"


@pytest.mark.skipif(ENVELOPE is None, reason="no envelope-*.pdf sample present")
def test_recipient_pdf_flag(tmp_path):
    out = tmp_path / "o.pdf"
    assert main(["--recipient-pdf", str(ENVELOPE), "-o", str(out)]) == 0
    assert "Eßer" in _text(out)
