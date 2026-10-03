"""The product shell every Watch page shares (#83).

The header leads with product navigation (Overview, Datasets, Changes,
Incidents), marks where the reader is, and keeps Docs and GitHub secondary.
A page that is not built yet stays in the navigation as plain text rather than
a link that goes nowhere. The demo states that it shows preview data as neutral
metadata, not as a warning, and the content area is wide enough for a product.
Asset and page URLs work from any depth, because detail pages live in nested
directories.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from types import ModuleType

import pytest

from kpubdata_watch.web.presentation import NAV_ITEMS, STATIC_DIR, environment

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "build_demo.py"
DEMO_CSS = STATIC_DIR / "demo.css"
CSS_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)


@pytest.fixture(scope="module")
def build_demo() -> ModuleType:
    spec = importlib.util.spec_from_file_location("build_demo", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def html(build_demo: ModuleType) -> str:
    rendered: str = build_demo.render()
    return rendered


def _css_rule(selector: str) -> str:
    css = CSS_COMMENT.sub("", DEMO_CSS.read_text(encoding="utf-8"))
    match = re.search(rf"(?m)^{re.escape(selector)}\s*\{{([^}}]*)\}}", css)
    assert match is not None, f"demo.css has no {selector} rule"
    return match.group(1)


def test_the_page_language_is_korean(html: str) -> None:
    assert '<html lang="ko">' in html


def test_primary_navigation_lists_the_four_surfaces_in_order(html: str) -> None:
    assert [label for _, label, _ in NAV_ITEMS] == ["Overview", "Datasets", "Changes", "Incidents"]
    nav = html[html.index('<nav class="primary-nav"') : html.index("</nav>")]
    positions = [nav.index(f">{label}<") for _, label, _ in NAV_ITEMS]
    assert positions == sorted(positions)


def test_the_current_page_is_marked(html: str) -> None:
    assert '<a class="nav-item" href="./" aria-current="page">Overview</a>' in html


def test_a_page_that_is_not_built_yet_is_not_a_link() -> None:
    page = (
        environment()
        .from_string('{% include "partials/nav.html" %}')
        .render(active_nav="overview", built_pages={"overview"}, root="")
    )
    for key, label, _ in NAV_ITEMS:
        if key == "overview":
            continue
        assert f'<span class="nav-item is-pending" aria-disabled="true">{label}</span>' in page


def test_a_built_page_becomes_a_link() -> None:
    page = (
        environment()
        .from_string('{% include "partials/nav.html" %}')
        .render(active_nav="overview", built_pages={"overview", "datasets"}, root="../")
    )
    assert '<a class="nav-item" href="../datasets/">Datasets</a>' in page


def test_product_navigation_comes_before_docs_and_github(html: str) -> None:
    header = html[html.index('<header class="shell-header">') : html.index("</header>")]
    assert header.index("Incidents") < header.index(">Docs<") < header.index(">GitHub<")


def test_the_brand_name_appears_once_in_the_header(html: str) -> None:
    header = html[html.index('<header class="shell-header">') : html.index("</header>")]
    assert header.count(">KPubData<") == 1
    assert header.count(">Watch<") == 1


def test_preview_data_is_neutral_metadata_with_the_snapshot_time(html: str) -> None:
    assert "demo-banner" not in html
    meta = html[html.index('class="preview-meta"') :]
    meta = meta[: meta.index("</p>")]
    assert "Preview data" in meta
    assert "고정된 예시 데이터" in meta
    assert "2026-10-02 21:15 KST" in meta
    assert "--status-" not in _css_rule(".preview-meta")


def test_the_content_area_is_a_wide_product_shell() -> None:
    css = CSS_COMMENT.sub("", DEMO_CSS.read_text(encoding="utf-8"))
    assert "720px" not in css
    assert "min(1180px, calc(100% - 48px))" in _css_rule(".product-shell")


def test_the_navigation_scrolls_inside_itself_on_a_narrow_screen() -> None:
    assert "overflow-x: auto" in _css_rule(".primary-nav")


def test_asset_and_page_urls_work_from_a_nested_page() -> None:
    template = environment().from_string(
        "{{ asset_url('demo.css') }}|{{ page_url('dataset', 'datago.apt_rent') }}|{{ page_url('overview') }}"
    )
    assert template.render(root="") == "static/demo.css|datasets/datago.apt_rent/|./"
    assert template.render(root="../../") == (
        "../../static/demo.css|../../datasets/datago.apt_rent/|../../"
    )


def test_every_link_in_the_shell_uses_the_url_helpers(html: str) -> None:
    for target in re.findall(r'(?:href|src)="([^"]+)"', html):
        if target.startswith(("https://", "#")):
            continue
        assert target in {"./", "docs/"} or target.startswith(
            ("static/", "datasets/", "incidents/", "changes/")
        ), target
