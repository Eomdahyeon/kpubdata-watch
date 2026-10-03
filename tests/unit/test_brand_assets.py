"""Watch shows one KPubData symbol everywhere, with a text lockup (#71).

The symbol is Studio's approved K, unchanged; CI compares it byte for byte with
kpubdata-studio's `symbol_light.svg` and `favicon.svg` (see ci.yml). Here the
checks are local: every place Watch shows the symbol uses the same file, and
the HTML lockup keeps `KPubData` above a neutral, lighter `Watch`.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
STATIC = REPO_ROOT / "src" / "kpubdata_watch" / "web" / "static"
SYMBOL = STATIC / "kpubdata-symbol.svg"
FAVICON = STATIC / "favicon.svg"
DOCS_SYMBOL = REPO_ROOT / "docs" / "assets" / "kpubdata-symbol.svg"
BASE_TEMPLATE = REPO_ROOT / "src" / "kpubdata_watch" / "web" / "templates" / "base.html"
DEMO_CSS = STATIC / "demo.css"
MKDOCS = REPO_ROOT / "mkdocs.yml"

CSS_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
BRAND_COLOUR = re.compile(r"var\(--(brand|data-accent)")


def _rule(selector: str) -> dict[str, str]:
    css = CSS_COMMENT.sub("", DEMO_CSS.read_text(encoding="utf-8"))
    match = re.search(rf"(?m)^{re.escape(selector)}\s*\{{([^}}]*)\}}", css)
    assert match is not None, f"demo.css has no {selector} rule"
    return dict(re.findall(r"([\w-]+)\s*:\s*([^;]+);", match.group(1)))


def test_favicon_and_docs_symbol_are_the_same_file_as_the_header_symbol() -> None:
    symbol = SYMBOL.read_bytes()
    assert FAVICON.read_bytes() == symbol
    assert DOCS_SYMBOL.read_bytes() == symbol


def test_docs_site_uses_the_symbol_as_logo_and_favicon() -> None:
    mkdocs = MKDOCS.read_text(encoding="utf-8")
    assert re.search(r"(?m)^\s+logo:\s*assets/kpubdata-symbol\.svg\s*$", mkdocs)
    assert re.search(r"(?m)^\s+favicon:\s*assets/kpubdata-symbol\.svg\s*$", mkdocs)


def test_header_shows_the_symbol_and_a_name_then_suffix_text_lockup() -> None:
    html = BASE_TEMPLATE.read_text(encoding="utf-8")
    assert "kpubdata-symbol.svg" in html
    name = html.index('class="brand-name">KPubData<')
    suffix = html.index('class="brand-suffix">Watch<')
    assert name < suffix


def test_suffix_is_neutral_and_lighter_than_the_name() -> None:
    lockup = _rule(".brand-lockup")
    suffix = _rule(".brand-suffix")
    assert suffix["color"].strip() == "var(--muted-foreground)"
    assert not BRAND_COLOUR.search(" ".join(suffix.values()))
    assert int(suffix["font-weight"]) < int(lockup["font-weight"])
