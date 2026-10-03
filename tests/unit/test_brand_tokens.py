"""`brand-v2.css` is the one token source for every Watch page (#70).

The colour blocks are copied from KPubData Studio and compared with Studio by
the drift gate (#72). This module checks what Watch itself relies on: every
theme block defines the full set of colour and status roles, Healthy never
borrows Fresh Mint, and the type scale, radius and density tokens exist so
templates and ``demo.css`` never need a literal size.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOKENS = REPO_ROOT / "src" / "kpubdata_watch" / "web" / "static" / "brand-v2.css"

CSS_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
BLOCK = re.compile(r"([^{}]+)\{([^{}]*)\}")
PROPERTY = re.compile(r"(--[\w-]+)\s*:\s*([^;]+);")

LIGHT = ':root, :root[data-theme="light"]'
DARK = ':root[data-theme="dark"]'
OS_DARK = ":root:not([data-theme])"
TYPE_AND_DENSITY = ":root"

COLOUR_ROLES = [
    "--brand-primary",
    "--brand-primary-foreground",
    "--brand-subtle",
    "--brand-text",
    "--data-accent",
    "--data-accent-strong",
    "--brand-secondary",
    "--brand-secondary-strong",
    "--background",
    "--foreground",
    "--card",
    "--card-foreground",
    "--muted",
    "--muted-foreground",
    "--border",
    "--input",
    "--ring",
]
STATUS_ROLES = [
    f"--status-{status}{suffix}"
    for status in ("success", "warning", "failure", "unknown")
    for suffix in ("", "-subtle", "-border")
]
TYPE_AND_DENSITY_TOKENS = [
    "--font-sans",
    "--font-mono",
    "--radius",
    "--radius-lg",
    "--radius-xl",
    "--radius-2xl",
    "--text-page-title",
    "--text-page-title--line-height",
    "--text-page-title--font-weight",
    "--text-section-title",
    "--text-section-title--line-height",
    "--text-section-title--font-weight",
    "--text-body",
    "--text-body--line-height",
    "--text-table",
    "--text-table--line-height",
    "--text-meta",
    "--text-meta--line-height",
    "--text-technical",
    "--text-technical--line-height",
    "--density-table-row",
    "--density-card-gap",
    "--shadow-card",
]


def _blocks() -> dict[str, dict[str, str]]:
    css = CSS_COMMENT.sub("", TOKENS.read_text(encoding="utf-8"))
    blocks: dict[str, dict[str, str]] = {}
    for match in BLOCK.finditer(css):
        selector = " ".join(match.group(1).split())
        found = PROPERTY.findall(match.group(2))
        properties = {name: " ".join(value.split()) for name, value in found}
        if properties:
            blocks.setdefault(selector, {}).update(properties)
    return blocks


@pytest.mark.parametrize("selector", [LIGHT, DARK, OS_DARK])
def test_every_theme_block_defines_every_colour_and_status_role(selector: str) -> None:
    block = _blocks()[selector]
    missing = [name for name in COLOUR_ROLES + STATUS_ROLES if name not in block]
    assert missing == [], f"{selector} is missing {missing}"


@pytest.mark.parametrize("selector", [LIGHT, DARK, OS_DARK])
def test_healthy_never_uses_fresh_mint(selector: str) -> None:
    block = _blocks()[selector]
    assert block["--status-success"] != block["--brand-secondary"]
    assert block["--status-success"] != block["--brand-secondary-strong"]


def test_type_scale_radius_and_density_tokens_exist() -> None:
    block = _blocks().get(TYPE_AND_DENSITY, {})
    missing = [name for name in TYPE_AND_DENSITY_TOKENS if name not in block]
    assert missing == [], f"brand-v2.css is missing {missing}"


def test_technical_identifiers_use_the_monospace_stack() -> None:
    block = _blocks()[TYPE_AND_DENSITY]
    assert "monospace" in block["--font-mono"]
    assert "monospace" not in block["--font-sans"]
