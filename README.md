# Postik — address & postage labels on sticker sheets

Turn recipient **addresses** + **postage** into a **print-ready DIN A4 PDF** laid out for
adhesive sticker sheets, positioned to the millimetre so nothing crosses the non-printable
margins. Built for small sellers who ship in envelopes — whatever you sell.

Each sticker carries the **sender** (left), the **recipient** (right), an optional **#PORTO**
postage block (below the recipient), and — for tracked orders — an embedded **Deutsche Post
Einschreiben Einwurf franking label** (middle). Defaults target Amazon's A4 sheets (4 large
labels); every measurement is an adjustable constant so you can calibrate after a test print.

Addresses can be typed/pasted, batch-loaded from a CSV/JSON manifest, or imported from an
order-export PDF — a **Cardmarket** importer (envelope / Sale PDFs) is included as one such
input adapter.

## Architecture

UI-agnostic **engine** + thin **frontends**, so a future GUI/web/Flutter app can reuse it:

```
src/postik/
  core/   models, sheets (geometry), layouts, config, render (ReportLab),
          label (PyMuPDF crop+embed), preview (PDF->PNG), pipeline (orchestration)
  io/     importers — cardmarket (order-export PDFs), manifest (CSV/JSON batch)
  cli/    argparse + interactive mode
  api/    FastAPI stub (generate / preview / parse / sheets / config)
```

## Setup (WSL + venv)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .            # makes `postik` importable + the `postik` command
```

## CLI usage

```bash
# Interactive
python -m postik -i

# One order from an order-export PDF (e.g. a Cardmarket envelope) + a porto code, from sticker 3
python -m postik --recipient-pdf envelope-123.pdf --porto CVNKP8VN --start 3 -o out.pdf

# High-value order with an Einschreiben franking label embedded
python -m postik --recipient-pdf "Sale_#123.pdf" --tracking Briefmarken.123.pdf

# Batch from a manifest (CSV or JSON)
python -m postik --manifest orders.json -o sheet.pdf

# Calibration sheet — print at 100% / Actual Size to tune the constants
python -m postik --calibration -o calibration.pdf

# Also dump a PNG preview of page 1
python -m postik --recipient-pdf envelope-123.pdf --preview preview.png
```

Print **without scaling** (100% / "Actual Size"). `#PORTO` is always rendered as two lines
(`#PORTO` then the code), same font size — required by the post-office scanner.

## Calibration

1. `python -m postik --calibration -o calibration.pdf` and print at 100%.
2. Lay it over a real sticker sheet; adjust the constants in
   [`core/sheets.py`](src/postik/core/sheets.py) — `margin_top`, `pitch_y`,
   `margin_left/right`, `sticker_w/h` — until the outlines match the die-cuts.
3. Zone widths / fonts (sender vs recipient vs #PORTO, label slot width) live in
   [`core/layouts.py`](src/postik/core/layouts.py).

## API stub

```bash
uvicorn postik.api.main:app --reload
# POST /parse/cardmarket (file upload) -> {"recipient": [...]}
# POST /generate (orders JSON)         -> application/pdf
# POST /preview  (orders JSON)         -> image/png
# GET  /sheets, /layouts, /config; PUT /config
```

## Tests

```bash
pytest
```

## Roadmap (future)

Full GUI (enter your own sender address, paste addresses, file chooser, live preview),
likely a **Flutter/Dart** frontend over the FastAPI engine; pluggable sticker sheets and
block layouts (already data-driven); optional Docker packaging of the backend.
