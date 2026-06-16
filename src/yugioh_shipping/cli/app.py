"""CLI: build a sticker-sheet PDF from flags or via interactive prompts.

Examples
--------
Interactive::

    python -m yugioh_shipping -i

One order from a Cardmarket envelope PDF + a porto code, starting at sticker 3::

    python -m yugioh_shipping --recipient-pdf envelope-123.pdf --porto CVNKP8VN --start 3 -o out.pdf

A high-value order with an Einschreiben franking label::

    python -m yugioh_shipping --recipient-pdf Sale_#123.pdf --tracking Briefmarken.123.pdf

Batch from a manifest::

    python -m yugioh_shipping --manifest orders.json -o sheet.pdf

Calibration sheet (print at 100% to tune the constants)::

    python -m yugioh_shipping --calibration -o calibration.pdf
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..core.config import load_config
from ..core.layouts import get_layout, list_layouts
from ..core.models import Address, Order, normalize_porto_code
from ..core.pipeline import build_calibration_pdf, build_pdf
from ..core.preview import render_page
from ..core.sheets import get_sheet, list_sheets
from ..io import cardmarket
from ..io.manifest import load_manifest


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="yugioh-shipping",
        description="Generate a print-ready DIN A4 shipping-sticker sheet for Cardmarket orders.",
    )
    p.add_argument("-i", "--interactive", action="store_true", help="step-by-step prompts")
    p.add_argument("--recipient-pdf", action="append", default=[], metavar="PDF",
                   help="Cardmarket envelope/Sale PDF (repeatable)")
    p.add_argument("--recipient", action="append", default=[], metavar="TEXT",
                   help="inline recipient; use \\n between lines (repeatable)")
    p.add_argument("--porto", action="append", default=[], metavar="CODE",
                   help="#PORTO code for the i-th flag-built order (repeatable)")
    p.add_argument("--tracking", action="append", default=[], metavar="PDF",
                   help="franking-label PDF for the i-th flag-built order (repeatable)")
    p.add_argument("--manifest", metavar="FILE", help="CSV/JSON batch of orders")
    p.add_argument("--sheet", metavar="ID", help="sticker sheet id (default from config)")
    p.add_argument("--layout", metavar="ID", help="layout id (default from config)")
    p.add_argument("--start", type=int, default=1, metavar="N",
                   help="start at sticker position N (1-based) on the first sheet")
    p.add_argument("-o", "--out", default="stickers.pdf", metavar="FILE", help="output PDF path")
    p.add_argument("--config", metavar="FILE", help="config file (sender address etc.)")
    p.add_argument("--sender", action="append", metavar="LINE",
                   help="override sender, one line per flag (repeatable)")
    p.add_argument("--preview", metavar="PNG", help="also write a PNG preview of page 1")
    p.add_argument("--calibration", action="store_true", help="emit the calibration sheet and exit")
    p.add_argument("--list-sheets", action="store_true", help="list available sheets/layouts and exit")
    return p


def _orders_from_flags(args) -> list[Order]:
    orders: list[Order] = []
    if args.manifest:
        orders.extend(load_manifest(args.manifest))

    flag_orders: list[Order] = []
    for pdf in args.recipient_pdf:
        path = Path(pdf)
        flag_orders.append(Order(recipient=cardmarket.auto_parse(path, name=path.name)))
    for text in args.recipient:
        flag_orders.append(Order(recipient=Address.from_text(text.replace("\\n", "\n"))))

    # apply porto/tracking positionally to the flag-built orders
    for idx, order in enumerate(flag_orders):
        if idx < len(args.porto) and args.porto[idx].strip():
            order.porto_code = normalize_porto_code(args.porto[idx])
        if idx < len(args.tracking) and args.tracking[idx].strip():
            order.tracking_label = Path(args.tracking[idx].strip())

    orders.extend(flag_orders)
    return orders


def _read_porto() -> str | None:
    """Read a porto code, accepting either the bare code or the pasted #PORTO block.

    When the whole block is pasted ("#PORTO\\nCVNKP8VN"), the first input line is just the
    "#PORTO" marker and the actual code arrives on the next (buffered) line -- consume it here
    so it doesn't leak into the next prompt. The marker is then stripped from the stored value.
    """
    raw = input("Porto code (paste the whole #PORTO block or just the code; blank = none): ").strip()
    if not raw:
        return None
    if raw.upper().lstrip("#").strip() == "PORTO":  # first line was only the marker
        try:
            raw = input("  code: ").strip()
        except EOFError:
            raw = ""
    return normalize_porto_code(raw)


def _interactive(capacity: int) -> tuple[list[Order], int]:
    print("Interactive mode. Enter one order at a time.\n")
    orders: list[Order] = []
    while True:
        print(f"--- Order {len(orders) + 1} ---")
        first = input("Recipient (path to a Cardmarket PDF, or paste the address; blank line ends a paste):\n").strip()
        candidate = Path(first)
        if first.lower().endswith(".pdf") and candidate.exists():
            addr = cardmarket.auto_parse(candidate, name=candidate.name)
            print("  parsed -> " + " / ".join(addr.lines))
        else:
            collected = [first] if first else []
            while True:
                more = input()
                if not more.strip():
                    break
                collected.append(more)
            addr = Address.from_text("\n".join(collected))
        if not addr:
            print("  (no address entered, skipping)\n")
            if orders:
                break
            continue

        porto = _read_porto()
        track = input("Tracking/franking label PDF, blank if none: ").strip() or None
        orders.append(Order(recipient=addr, porto_code=porto, tracking_label=Path(track) if track else None))

        if input("Add another order? [y/N]: ").strip().lower() not in ("y", "yes"):
            break
        print()

    raw = input(f"Start at which sticker position? 1-{capacity} [1]: ").strip()
    start = int(raw) if raw else 1
    return orders, start


def main(argv: list[str] | None = None) -> int:
    """Entry point. Catches Ctrl+C / Ctrl+D so they exit quietly instead of a traceback."""
    try:
        return _run(argv)
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.", file=sys.stderr)
        return 130  # conventional exit code for SIGINT


def _run(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.list_sheets:
        print("Sheets:")
        for s in list_sheets():
            print(f"  {s.id:<16} {s.name}  ({s.rows}x{s.cols}, {s.sticker_w:.0f}x{s.sticker_h:.0f} mm)")
        print("Layouts:")
        for lo in list_layouts():
            print(f"  {lo.id:<16} {lo.name}")
        return 0

    cfg = load_config(args.config)
    sheet = get_sheet(args.sheet or cfg.default_sheet_id)
    layout = get_layout(args.layout or cfg.default_layout_id)
    sender_lines = args.sender if args.sender else cfg.sender_lines
    out = Path(args.out)

    if args.calibration:
        out.write_bytes(build_calibration_pdf(sheet))
        print(f"Wrote calibration sheet -> {out}  (print at 100% / Actual Size)")
        return 0

    orders = _orders_from_flags(args)
    start = args.start
    if args.interactive or not orders:
        orders, start = _interactive(sheet.capacity)

    if not orders:
        print("No orders to render.", file=sys.stderr)
        return 1

    try:
        pdf_bytes = build_pdf(orders, sheet, layout, sender_lines, start_position=start)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    out.write_bytes(pdf_bytes)
    print(f"Wrote {len(orders)} sticker(s) starting at position {start} -> {out}")

    if args.preview:
        Path(args.preview).write_bytes(render_page(pdf_bytes, page=0))
        print(f"Wrote preview -> {args.preview}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
