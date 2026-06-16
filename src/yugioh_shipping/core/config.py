"""User configuration: the sender (your own) address and default sheet/layout choices.

Stored as JSON so a future GUI's "enter your own address" screen just edits this file. The
default sender is the project owner's address; override via the CLI ``--config`` flag or the
API ``PUT /config`` endpoint.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .layouts import DEFAULT_LAYOUT_ID
from .sheets import DEFAULT_SHEET_ID

DEFAULT_SENDER: list[str] = [
    "Gerrit Schelling",
    "Am Flottmoorpark 22",
    "24568 Kaltenkirchen",
    "Germany",
]


@dataclass
class Config:
    sender_lines: list[str] = field(default_factory=lambda: list(DEFAULT_SENDER))
    default_sheet_id: str = DEFAULT_SHEET_ID
    default_layout_id: str = DEFAULT_LAYOUT_ID


def default_config() -> Config:
    return Config()


def default_config_path() -> Path:
    """Per-user config location (XDG on Linux/WSL, %APPDATA% on Windows)."""
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "yugioh_shipping" / "config.json"


def load_config(path: str | Path | None = None) -> Config:
    """Load config from ``path`` (or the default location). Missing file -> defaults."""
    p = Path(path) if path else default_config_path()
    if not p.exists():
        return default_config()
    data = json.loads(p.read_text(encoding="utf-8"))
    cfg = default_config()
    if isinstance(data.get("sender_lines"), list):
        cfg.sender_lines = [str(x) for x in data["sender_lines"]]
    cfg.default_sheet_id = str(data.get("default_sheet_id", cfg.default_sheet_id))
    cfg.default_layout_id = str(data.get("default_layout_id", cfg.default_layout_id))
    return cfg


def save_config(cfg: Config, path: str | Path | None = None) -> Path:
    p = Path(path) if path else default_config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(asdict(cfg), ensure_ascii=False, indent=2), encoding="utf-8")
    return p
