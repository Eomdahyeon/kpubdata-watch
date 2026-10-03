"""Brand v2 UI primitives render the same way on every Watch page (#73).

Each primitive is a Jinja macro in `templates/components/primitives.html`,
styled by `static/components.css`. The tests render each macro on its own and
check what a reader relies on: a status is always an icon, a text label and a
colour together; Unknown never looks like Critical; a Change is informational
and never takes a health colour; and the stylesheet uses tokens only.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from kpubdata_watch.web.presentation import (
    CHANGE_ICON,
    HEALTH_META,
    HEALTH_ORDER,
    STATIC_DIR,
    TEMPLATES_DIR,
    environment,
)

COMPONENTS_CSS = STATIC_DIR / "components.css"
PRIMITIVES = TEMPLATES_DIR / "components" / "primitives.html"

CSS_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
HEX_COLOR = re.compile(r"#[0-9a-fA-F]{3,8}\b")


def render(call: str, **context: object) -> str:
    source = '{% import "components/primitives.html" as ui with context %}' + call
    return environment().from_string(source).render(**context)


def _css_rule(selector: str) -> str:
    css = CSS_COMMENT.sub("", COMPONENTS_CSS.read_text(encoding="utf-8"))
    match = re.search(rf"(?m)^{re.escape(selector)}\s*\{{([^}}]*)\}}", css)
    assert match is not None, f"components.css has no {selector} rule"
    return match.group(1)


@pytest.mark.parametrize("health", HEALTH_ORDER)
def test_status_badge_shows_icon_text_and_a_health_class(health: str) -> None:
    html = render("{{ ui.status_badge(health) }}", health=health)
    meta = HEALTH_META[health]
    assert f'class="status-badge status-{health}"' in html
    assert f'<span class="status-icon" aria-hidden="true">{meta["icon"]}</span>' in html
    assert f'<span class="status-text">{meta["label"]}</span>' in html


def test_unknown_and_critical_differ_in_icon_text_and_colour() -> None:
    assert HEALTH_META["unknown"]["icon"] != HEALTH_META["critical"]["icon"]
    assert HEALTH_META["unknown"]["label"] != HEALTH_META["critical"]["label"]
    assert "--status-unknown" in _css_rule(".status-badge.status-unknown")
    assert "--status-failure" in _css_rule(".status-badge.status-critical")


def test_health_summary_lists_every_state_in_order() -> None:
    counts = {"healthy": 8, "degraded": 4, "critical": 2, "unknown": 1}
    html = render("{{ ui.health_summary(counts) }}", counts=counts)
    positions = [html.index(f"count-{key}") for key in HEALTH_ORDER]
    assert positions == sorted(positions)
    for key in HEALTH_ORDER:
        assert HEALTH_META[key]["label"] in html
        assert f'<span class="count-value">{counts[key]}</span>' in html


def test_change_badge_is_informational_and_never_a_health_colour() -> None:
    html = render("{{ ui.change_badge() }}")
    assert CHANGE_ICON in html and "Changed" in html
    assert "--status-" not in _css_rule(".change-badge")
    assert "--status-" not in _css_rule(".dataset-change")


def test_dataset_row_shows_name_provider_status_issue_and_change() -> None:
    row = {
        "name": "아파트 전월세 실거래가",
        "provider": "국토교통부",
        "health": "critical",
        "checked_label": "21:14 KST",
        "checked_exact": "2026-10-02T21:14:40+09:00",
        "issue": "Breaking contract change",
        "change": "Contract changed",
    }
    html = render("{{ ui.dataset_row(row) }}", row=row)
    assert 'class="dataset-row status-critical"' in html
    for text in (row["name"], row["provider"], row["issue"], row["change"], "Critical"):
        assert text in html
    assert CHANGE_ICON in html


def test_timestamp_carries_a_machine_readable_time() -> None:
    html = render('{{ ui.timestamp("21:14 KST", "2026-10-02T21:14:40+09:00") }}')
    assert '<time class="timestamp" datetime="2026-10-02T21:14:40+09:00"' in html
    assert ">21:14 KST</time>" in html


def test_metadata_is_a_description_list_with_monospace_identifiers() -> None:
    items = [("Provider", "국토교통부", False), ("Dataset ID", "datago.apt_rent", True)]
    html = render("{{ ui.metadata(items) }}", items=items)
    assert html.count("<dt>") == 2 and html.count("<dd") == 2
    assert '<dd class="technical-id">datago.apt_rent</dd>' in html
    assert "--font-mono" in _css_rule(".technical-id")


def test_panel_is_a_labelled_section_with_a_heading() -> None:
    html = render('{% call ui.panel("Active Issues", "active-issues") %}body{% endcall %}')
    assert '<section class="panel" aria-labelledby="active-issues">' in html
    assert '<h2 class="panel-title" id="active-issues">Active Issues</h2>' in html
    assert "body" in html


def test_contract_diff_marks_each_change_in_text_not_only_colour() -> None:
    html = render(
        "{{ ui.contract_diff(added, removed, changed) }}",
        added=["productEngName:string"],
        removed=["addr2:string"],
        changed=["dealAmount:string → int"],
    )
    for kind, sign, field in (
        ("added", "+", "productEngName:string"),
        ("removed", "−", "addr2:string"),
        ("changed", "~", "dealAmount:string → int"),
    ):
        assert f'<li class="diff-{kind}">' in html
        assert f'<span class="diff-sign" aria-hidden="true">{sign}</span>' in html
        assert f'<span class="sr-only">{kind.capitalize()}: </span>' in html
        assert f"<code>{field}</code>" in html
    assert "--status-" not in _css_rule(".diff-added")


def test_empty_state_shows_its_message() -> None:
    html = render('{{ ui.empty_state("No active issues") }}')
    assert '<p class="empty-state">No active issues</p>' in html


def test_components_css_uses_tokens_only_and_respects_reduced_motion() -> None:
    css = CSS_COMMENT.sub("", COMPONENTS_CSS.read_text(encoding="utf-8"))
    assert not HEX_COLOR.search(css), "components.css has a raw hex colour; use var(--...)"
    assert "@media (prefers-reduced-motion: reduce)" in css


def test_primitives_template_has_no_raw_hex() -> None:
    assert not HEX_COLOR.search(PRIMITIVES.read_text(encoding="utf-8"))


def test_base_template_links_components_css_after_the_tokens() -> None:
    base = (TEMPLATES_DIR / "base.html").read_text(encoding="utf-8")
    assert base.index("brand-v2.css") < base.index("components.css") < base.index("demo.css")


def test_raw_markup_is_escaped() -> None:
    html = render("{{ ui.empty_state(message) }}", message="<script>x</script>")
    assert "<script>" not in html


def test_change_icon_is_the_info_glyph() -> None:
    assert CHANGE_ICON == "ⓘ"


def test_module_paths_point_into_the_package() -> None:
    assert Path(TEMPLATES_DIR).name == "templates"
    assert Path(STATIC_DIR).name == "static"
