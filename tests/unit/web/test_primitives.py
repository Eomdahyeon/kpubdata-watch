"""Brand v2 UI primitives render the same way on every Watch page (#73).

Each primitive is a Jinja macro in `templates/components/primitives.html`,
styled by `static/components.css`. The tests render each macro on its own and
check what a reader relies on: a status is always an icon, a text label and a
colour together; Unknown never looks like Critical; a Change is informational
and never takes a health colour; and the stylesheet uses tokens only.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pytest

from kpubdata_watch.web.presentation import (
    CHANGE_ICON,
    CHECK_META,
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
    ratio = {"healthy": 53, "degraded": 27, "critical": 13, "unknown": 7}
    html = render(
        "{{ ui.health_summary(headline, status_ratio, counts) }}",
        headline="15개 중 7개에 문제가 있습니다.",
        status_ratio=ratio,
        counts=counts,
    )
    assert '<p class="health-headline">15개 중 7개에 문제가 있습니다.</p>' in html
    positions = [html.index(f"count-{key}") for key in HEALTH_ORDER]
    assert positions == sorted(positions)
    for key in HEALTH_ORDER:
        assert HEALTH_META[key]["label"] in html
        assert f'<span class="count-value">{counts[key]}</span>' in html


def test_health_summary_ratio_bar_is_decorative_and_skips_zero_segments() -> None:
    counts = {"healthy": 15, "degraded": 0, "critical": 0, "unknown": 0}
    ratio = {"healthy": 100, "degraded": 0, "critical": 0, "unknown": 0}
    html = render(
        "{{ ui.health_summary(headline, status_ratio, counts) }}",
        headline="15개 모두 정상입니다.",
        status_ratio=ratio,
        counts=counts,
    )
    assert '<div class="status-ratio-bar" aria-hidden="true">' in html
    assert html.count("status-ratio-segment--") == 1
    assert 'class="status-ratio-segment status-ratio-segment--healthy" style="width: 100%"' in html


@pytest.mark.parametrize(
    ("status", "summary"),
    [
        ("pass", None),
        ("warn", "지연 42분"),
        ("fail", "HTTP 500"),
        ("unknown", None),
        ("not_applicable", "freshness.enabled = false"),
    ],
)
def test_check_matrix_renders_every_check_state(status: str, summary: str | None) -> None:
    from kpubdata_watch.api.read_models.public import CheckResult, Checks

    checks = Checks(
        availability=CheckResult(status=status, summary=summary),
        freshness=CheckResult(status="pass"),
        contract=CheckResult(status="pass"),
        quality=CheckResult(status="pass"),
    )
    html = render("{{ ui.check_matrix(checks) }}", checks=checks)
    assert f'class="check-cell check-cell-{status}"' in html
    label = f"Availability: {CHECK_META[status]['label']}"
    if summary:
        label += f" · {summary}"
    assert f'title="{label}"' in html
    assert f'aria-label="{label}"' in html
    assert html.count('class="check-cell ') == 4


def test_check_matrix_not_applicable_uses_neutral_tokens_not_a_status_colour() -> None:
    rule = _css_rule(".check-cell-not_applicable")
    assert "--status-" not in rule
    assert "--muted" in rule and "--border" in rule


def test_change_badge_is_informational_and_never_a_health_colour() -> None:
    html = render("{{ ui.change_badge() }}")
    assert CHANGE_ICON in html and "Changed" in html
    assert "--status-" not in _css_rule(".change-badge")
    assert "--status-" not in _css_rule(".dataset-change")


def _dataset_row() -> dict[str, str]:
    """The shape `scripts/build_demo.py::dataset_rows` actually produces (issue 96):
    `checked_label` (visible text), `checked_at` (the ISO-8601 instant) and
    `checked_exact` (the KST-formatted string, for a title only).
    """
    return {
        "name": "아파트 전월세 실거래가",
        "provider": "국토교통부",
        "health": "critical",
        "checked_label": "Checked 21:14 KST",
        "checked_at": "2026-10-02T21:14:40+09:00",
        "checked_exact": "2026-10-02 21:14:40 KST",
        "issue": "Breaking contract change",
        "change": "Contract changed",
    }


def test_dataset_row_shows_name_provider_status_issue_and_change() -> None:
    row = _dataset_row()
    html = render("{{ ui.dataset_row(row) }}", row=row)
    assert 'class="dataset-row status-critical"' in html
    for text in (row["name"], row["provider"], row["issue"], row["change"], "Critical"):
        assert text in html
    assert CHANGE_ICON in html


def test_dataset_row_wires_the_exact_checked_time_into_a_machine_readable_time() -> None:
    """issue 96: `checked_at`, the exact instant, must land in `datetime=`, not `title=`."""
    row = _dataset_row()
    html = render("{{ ui.dataset_row(row) }}", row=row)
    assert (
        '<time class="timestamp" datetime="2026-10-02T21:14:40+09:00" '
        'title="2026-10-02 21:14:40 KST">Checked 21:14 KST</time>'
    ) in html
    match = re.search(r'<time class="timestamp" datetime="([^"]+)"', html)
    assert match is not None, "dataset_row did not render a <time datetime=...> element"
    assert datetime.fromisoformat(match.group(1)) == datetime.fromisoformat(row["checked_at"])


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


def _history_day(iso: str, health: str) -> object:
    from datetime import date as _date

    from kpubdata_watch.api.read_models.public import HistoryDay

    return HistoryDay(date=_date.fromisoformat(iso), health=health)


def test_history_grid_reuses_history_day_markup_with_a_date_and_health_label() -> None:
    rows = [
        {
            "dataset_id": "x",
            "name": "X",
            "provider": "Y",
            "health": "degraded",
            "abnormal_days": 1,
            "cells": [
                _history_day("2026-09-21", "healthy"),
                _history_day("2026-09-22", "degraded"),
            ],
        }
    ]
    html = render("{{ ui.history_grid(rows) }}", rows=rows, built_pages={"dataset"})
    assert '<a href="datasets/x/">X</a>' in html
    assert '<td class="history-day status-degraded"' in html
    assert 'aria-label="2026-09-22 Degraded"' in html
    assert "비정상 1일" in html
    assert 'colspan="2"' in html


def test_history_grid_without_the_dataset_page_is_not_a_link() -> None:
    rows = [
        {
            "dataset_id": "x",
            "name": "X",
            "provider": "Y",
            "health": "healthy",
            "abnormal_days": 0,
            "cells": [_history_day("2026-09-21", "healthy")],
        }
    ]
    html = render("{{ ui.history_grid(rows) }}", rows=rows, built_pages=frozenset())
    assert "<a href=" not in html
    assert '<th scope="row">X</th>' in html


def test_evidence_chart_renders_nothing_when_the_view_is_none() -> None:
    assert render("{{ ui.evidence_chart(view) }}", view=None).strip() == ""


def test_evidence_chart_svg_carries_role_img_aria_label_and_a_title() -> None:
    view = {
        "kind": "quality_volume",
        "band_x": 50.0,
        "band_width": 20.0,
        "dot_x": 30.0,
        "dot_tone": "degraded",
        "percent_label": "−40%",
        "summary": "Expected 10,000–10,500 records, observed 6,000 (−40%).",
    }
    html = render("{{ ui.evidence_chart(view) }}", view=view)
    assert 'role="img"' in html
    assert f'aria-label="{view["summary"]}"' in html
    assert f"<title>{view['summary']}</title>" in html
    assert 'class="evidence-mark tone-degraded"' in html
    assert "−40%" in html


def test_evidence_chart_for_contract_reuses_contract_diff_chips() -> None:
    view = {"kind": "contract", "added": ["a:string"], "removed": ["b:string"], "summary": "s"}
    html = render("{{ ui.evidence_chart(view) }}", view=view)
    assert '<li class="diff-added">' in html and "a:string" in html
    assert '<li class="diff-removed">' in html and "b:string" in html
    assert "<svg" not in html


def test_daily_counts_bar_renders_one_column_per_day_with_a_label() -> None:
    days = [
        {
            "date": "2026-09-21",
            "heights": {"degraded": 10, "critical": 0, "unknown": 0},
            "label": "d1",
        },
        {
            "date": "2026-09-22",
            "heights": {"degraded": 0, "critical": 0, "unknown": 0},
            "label": "d2",
        },
    ]
    html = render("{{ ui.daily_counts_bar(days) }}", days=days)
    assert html.count('class="daily-bar-day"') == 2
    assert 'title="d1"' in html and 'aria-label="d1"' in html
    assert 'class="daily-bar-segment daily-bar-segment--degraded"' in html
    assert "height: 10px" in html
    # A day with nothing abnormal draws no segment at all.
    assert html.count("daily-bar-segment--") == 1
