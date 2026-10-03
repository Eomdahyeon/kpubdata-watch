"""Presentation vocabulary shared by every Watch page (#73).

The health labels and icons, the Change glyph and the Jinja environment live
here so that the fixture demo (`scripts/build_demo.py`) and the server-rendered
service use the same primitives from `templates/components/primitives.html`.
A health state always shows its icon and text label together with its colour,
never colour alone (docs/UI.md, PRD §53).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from jinja2 import Environment, FileSystemLoader, select_autoescape

WEB_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"

HEALTH_ORDER = ("healthy", "degraded", "critical", "unknown")
HEALTH_META: dict[str, dict[str, str]] = {
    "healthy": {"label": "Healthy", "icon": "●"},
    "degraded": {"label": "Degraded", "icon": "▲"},
    "critical": {"label": "Critical", "icon": "✕"},
    "unknown": {"label": "Unknown", "icon": "?"},
}
# A Change is informational: the neutral "info" glyph, never a health colour
# (PRD §46, §53).
CHANGE_ICON = "ⓘ"

KST = ZoneInfo("Asia/Seoul")


def kst_time(moment: datetime) -> str:
    """`21:12 KST`: a clock time, which stays true however late a static page is read."""
    return moment.astimezone(KST).strftime("%H:%M KST")


def kst_datetime(moment: datetime) -> str:
    """`2026-10-02 21:12:43 KST`: the exact time, for a title or tooltip."""
    return moment.astimezone(KST).strftime("%Y-%m-%d %H:%M:%S KST")


def environment(templates_dir: Path = TEMPLATES_DIR) -> Environment:
    """Return a Jinja environment with the presentation vocabulary as globals."""
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html"]),
    )
    env.globals.update(
        health_order=HEALTH_ORDER,
        health_meta=HEALTH_META,
        change_icon=CHANGE_ICON,
    )
    return env
