"""FastAPI stub endpoints, driven with the in-process TestClient."""

from __future__ import annotations

import base64

import fitz
import pytest
from fastapi.testclient import TestClient

from samples import ENVELOPE, LABEL

from postik.api.main import app

client = TestClient(app)
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def test_get_sheets():
    r = client.get("/sheets")
    assert r.status_code == 200
    assert any(s["id"] == "amazon_a4_4up" for s in r.json())


def test_get_layouts():
    r = client.get("/layouts")
    assert r.status_code == 200
    assert any(lo["id"] == "default" for lo in r.json())


def test_get_config_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))  # isolate from any real config
    r = client.get("/config")
    assert r.status_code == 200
    body = r.json()
    assert body["default_sheet_id"] == "amazon_a4_4up"
    assert isinstance(body["sender_lines"], list)


def test_put_config_persists_and_reads_back(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    r = client.put("/config", json={"sender_lines": ["Me", "Street 1", "12345 City", "Germany"]})
    assert r.status_code == 200
    assert (tmp_path / "postik" / "config.json").exists()
    assert client.get("/config").json()["sender_lines"][0] == "Me"


def test_generate_returns_pdf_with_single_porto():
    payload = {
        "orders": [
            {"recipient": ["Max", "Str 1", "12345 Berlin", "Germany"], "porto_code": "#PORTO\nCVNKP8VN"}
        ],
        "start_position": 2,
    }
    r = client.post("/generate", json=payload)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"
    text = "\n".join(p.get_text() for p in fitz.open(stream=r.content, filetype="pdf"))
    assert text.count("#PORTO") == 1
    assert text.count("CVNKP8VN") == 1


def test_preview_returns_png():
    payload = {"orders": [{"recipient": ["Max", "Str 1", "12345 Berlin", "Germany"]}]}
    r = client.post("/preview", json=payload)
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    assert r.content[:8] == PNG_MAGIC


def test_generate_invalid_start_position_is_422():
    r = client.post("/generate", json={"orders": [{"recipient": ["A"]}], "start_position": 99})
    assert r.status_code == 422


def test_generate_missing_recipient_is_422():
    r = client.post("/generate", json={"orders": [{}]})
    assert r.status_code == 422  # pydantic validation: recipient is required


def test_parse_cardmarket_rejects_non_pdf():
    r = client.post("/parse/cardmarket", files={"file": ("x.pdf", b"not a real pdf", "application/pdf")})
    assert r.status_code == 422


@pytest.mark.skipif(ENVELOPE is None, reason="no envelope-*.pdf sample present")
def test_parse_cardmarket_ok():
    r = client.post(
        "/parse/cardmarket",
        files={"file": (ENVELOPE.name, ENVELOPE.read_bytes(), "application/pdf")},
    )
    assert r.status_code == 200
    assert any("Eßer" in ln for ln in r.json()["recipient"])


@pytest.mark.skipif(LABEL is None, reason="no Briefmarken*.pdf sample present")
def test_generate_with_tracking_label_b64():
    b64 = base64.b64encode(LABEL.read_bytes()).decode()
    payload = {"orders": [{"recipient": ["Max", "Str 1", "12345 Berlin", "Germany"], "tracking_label_b64": b64}]}
    r = client.post("/generate", json=payload)
    assert r.status_code == 200
    assert r.content[:4] == b"%PDF"
