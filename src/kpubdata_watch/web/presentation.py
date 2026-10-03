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

from jinja2 import Environment, FileSystemLoader, pass_context, select_autoescape
from jinja2.runtime import Context

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
# A check result (pass, warn, fail, unknown, not_applicable) borrows the health
# colour it implies and always carries its own icon and label (#86).
CHECK_META: dict[str, dict[str, str]] = {
    "pass": {"label": "Pass", "icon": "●", "tone": "healthy"},
    "warn": {"label": "Warn", "icon": "▲", "tone": "degraded"},
    "fail": {"label": "Fail", "icon": "✕", "tone": "critical"},
    "unknown": {"label": "Unknown", "icon": "?", "tone": "unknown"},
    "not_applicable": {"label": "Not applicable", "icon": "–", "tone": "neutral"},
}
CHECK_LABELS = {
    "availability": "Availability",
    "freshness": "Freshness",
    "contract": "Contract",
    "quality": "Quality",
}
# A Change is informational: the neutral "info" glyph, never a health colour
# (PRD §46, §53).
CHANGE_ICON = "ⓘ"

# The product navigation (#83): (key, label, path below the site root).
NAV_ITEMS: tuple[tuple[str, str, str], ...] = (
    ("overview", "Overview", ""),
    ("datasets", "Datasets", "datasets/"),
    ("changes", "Changes", "changes/"),
    ("incidents", "Incidents", "incidents/"),
)
# Pages that take an identifier live one directory deeper.
_ENTITY_PATHS = {"dataset": "datasets/{}/", "incident": "incidents/{}/", "change": "changes/{}/"}
_PAGE_PATHS = {key: path for key, _, path in NAV_ITEMS}

KST = ZoneInfo("Asia/Seoul")


def kst_time(moment: datetime) -> str:
    """`21:12 KST`: a clock time, which stays true however late a static page is read."""
    return moment.astimezone(KST).strftime("%H:%M KST")


def kst_datetime(moment: datetime) -> str:
    """`2026-10-02 21:12:43 KST`: the exact time, for a title or tooltip."""
    return moment.astimezone(KST).strftime("%Y-%m-%d %H:%M:%S KST")


def kst_minute(moment: datetime) -> str:
    """`2026-10-02 21:15 KST`: a date and clock time to the minute."""
    return moment.astimezone(KST).strftime("%Y-%m-%d %H:%M KST")


@pass_context
def asset_url(context: Context, name: str) -> str:
    """A static asset's URL from the page being rendered.

    Every page passes `root`, the relative path back to the site root ("" for the
    overview, "../../" for a dataset detail), so the same templates work at any
    depth and under any base path, such as GitHub Pages' `/kpubdata-watch/`.
    """
    return f"{context.get('root', '')}static/{name}"


@pass_context
def page_url(context: Context, kind: str, identifier: str | None = None) -> str:
    """A product page's URL from the page being rendered, for example `datasets/<id>/`."""
    path = _ENTITY_PATHS[kind].format(identifier) if identifier else _PAGE_PATHS[kind]
    return f"{context.get('root', '')}{path}" or "./"


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
        check_meta=CHECK_META,
        check_labels=CHECK_LABELS,
        nav_items=NAV_ITEMS,
        asset_url=asset_url,
        page_url=page_url,
    )
    env.filters.update(kst_time=kst_time, kst_minute=kst_minute, kst_datetime=kst_datetime)
    return env
