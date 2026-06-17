"""FastAPI stub exposing the engine. JSON + multipart friendly so a Flutter/Dart or web
client can drive it directly. No auth/persistence -- it only validates the boundary.

Endpoints:
    GET  /sheets, GET /layouts        -> available specs (for frontend dropdowns)
    GET  /config, PUT /config         -> read / update the sender address etc.
    POST /parse/cardmarket            -> upload an envelope/Sale PDF, get recipient lines
    POST /generate                    -> orders JSON -> application/pdf
    POST /preview                     -> orders JSON -> image/png (one page)
"""

from __future__ import annotations

import base64
from dataclasses import asdict

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from ..core.config import Config, default_config_path, load_config, save_config
from ..core.layouts import get_layout, list_layouts
from ..core.models import Address, Order, normalize_porto_code
from ..core.pipeline import build_pdf
from ..core.preview import render_page
from ..core.sheets import get_sheet, list_sheets
from ..io import cardmarket

app = FastAPI(title="Postik", version="0.1.0")

# Dev-permissive CORS so the Flutter Web client (served from a different localhost port) can
# call the API. Tighten allow_origins for any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class OrderIn(BaseModel):
    recipient: list[str]
    porto_code: str | None = None
    tracking_label_b64: str | None = None  # base64 of the franking-label PDF (optional)


class GenerateRequest(BaseModel):
    orders: list[OrderIn]
    sheet_id: str | None = None
    layout_id: str | None = None
    start_position: int = 1


class PreviewRequest(GenerateRequest):
    page: int = 0
    dpi: int = 150


class ConfigIn(BaseModel):
    sender_lines: list[str] | None = None
    default_sheet_id: str | None = None
    default_layout_id: str | None = None


def _to_orders(items: list[OrderIn]) -> list[Order]:
    orders: list[Order] = []
    for it in items:
        tracking = base64.b64decode(it.tracking_label_b64) if it.tracking_label_b64 else None
        orders.append(Order(recipient=Address(lines=it.recipient), porto_code=normalize_porto_code(it.porto_code), tracking_label=tracking))
    return orders


def _resolve(req: GenerateRequest):
    cfg = load_config()
    sheet = get_sheet(req.sheet_id or cfg.default_sheet_id)
    layout = get_layout(req.layout_id or cfg.default_layout_id)
    return cfg, sheet, layout


@app.get("/sheets")
def get_sheets():
    return [asdict(s) for s in list_sheets()]


@app.get("/layouts")
def get_layouts():
    return [asdict(lo) for lo in list_layouts()]


@app.get("/config")
def get_config():
    return asdict(load_config())


@app.put("/config")
def put_config(body: ConfigIn):
    cfg = load_config()
    if body.sender_lines is not None:
        cfg.sender_lines = body.sender_lines
    if body.default_sheet_id is not None:
        cfg.default_sheet_id = body.default_sheet_id
    if body.default_layout_id is not None:
        cfg.default_layout_id = body.default_layout_id
    path = save_config(cfg)
    return {"saved_to": str(path), "config": asdict(cfg)}


@app.post("/parse/cardmarket")
async def parse_cardmarket(file: UploadFile = File(...)):
    data = await file.read()
    try:
        address = cardmarket.auto_parse(data, name=file.filename)
    except Exception as exc:  # noqa: BLE001 - surface parse errors to the client
        raise HTTPException(status_code=422, detail=f"could not parse PDF: {exc}") from exc
    return JSONResponse({"recipient": address.lines})


@app.post("/generate")
def generate(req: GenerateRequest):
    cfg, sheet, layout = _resolve(req)
    try:
        pdf = build_pdf(_to_orders(req.orders), sheet, layout, cfg.sender_lines, req.start_position)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": "inline; filename=stickers.pdf"})


@app.post("/preview")
def preview(req: PreviewRequest):
    cfg, sheet, layout = _resolve(req)
    try:
        pdf = build_pdf(_to_orders(req.orders), sheet, layout, cfg.sender_lines, req.start_position)
        png = render_page(pdf, page=req.page, dpi=req.dpi)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return Response(content=png, media_type="image/png")
