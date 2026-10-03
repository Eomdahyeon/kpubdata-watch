"""The Overview answers "what is wrong right now?" first (#84, issue 110).

Order: page header, Health summary (headline + ratio bar + counts), Active
Issues, Recent Changes, then a dataset x check matrix. Critical issues come
before Degraded ones and every issue is above the healthy datasets. A Change
looks different from an Incident. When there is no active issue the panel
says so. An active issue also carries History's own abnormal-day count. The
matrix preview shows part of the list and links to the full catalog once
that page exists; until then the Overview keeps every dataset so nothing is
hidden.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
from types import ModuleType

import pytest

from kpubdata_watch.web.presentation import duration

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "build_demo.py"
FIXTURES = REPO_ROOT / "demo" / "fixtures"


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


def panel(html: str, heading: str) -> str:
    start = html.index(f">{heading}</h2>")
    return html[start : html.find("</section>", start)]


def test_sections_appear_in_the_issue_first_order(html: str) -> None:
    order = [
        "<h1>Public Data Health</h1>",
        'class="summary-counts"',
        ">Active Issues</h2>",
        ">Recent Changes</h2>",
        ">Datasets</h2>",
    ]
    positions = [html.index(marker) for marker in order]
    assert positions == sorted(positions)


def test_active_issues_list_critical_before_degraded(html: str) -> None:
    issues = panel(html, "Active Issues")
    severities = re.findall(r'<li class="issue-row severity-(\w+)"', issues)
    assert severities == sorted(severities, key=["critical", "warning", "info"].index)
    assert severities[0] == "critical" and "warning" in severities


def test_an_issue_shows_dataset_check_summary_first_detected_and_duration(html: str) -> None:
    issues = panel(html, "Active Issues")
    name = "공공자전거(따릉이) 대여소 현황"
    row = next(item for item in issues.split('<li class="issue-row ')[1:] if name in item)
    assert "Availability" in row
    assert "HTTP 500 응답이 3회 연속 관측됐습니다." in row
    assert "First detected 20:46 KST" in row
    assert "31m" in row  # started 20:44, snapshot 21:15
    assert 'href="datasets/seoul.public_bike/"' in row
    # seoul.public_bike's history has 1 abnormal day out of 30 (#109's own count,
    # reused rather than re-derived here); the row also links to History (#110).
    assert "최근 30일 중 비정상 1일" in row
    assert 'href="history/"' in row


def test_an_issue_with_evidence_shows_its_mini_chart_above_the_meta_line(html: str) -> None:
    """#111: the chart sits between the issue text and "First detected ..."."""
    issues = panel(html, "Active Issues")
    name = "공공자전거(따릉이) 대여소 현황"
    row = next(item for item in issues.split('<li class="issue-row ')[1:] if name in item)
    assert '<div class="evidence-chart">' in row
    assert row.index('<div class="evidence-chart">') < row.index("First detected")


def test_the_issue_count_matches_the_active_incidents(html: str) -> None:
    incidents = json.loads((FIXTURES / "incidents.json").read_text(encoding="utf-8"))
    active = [i for i in incidents if i["status"] in {"open", "ongoing"}]
    issues = panel(html, "Active Issues")
    assert len(re.findall(r'<li class="issue-row ', issues)) == len(active)
    assert f'<span class="panel-count">{len(active)}</span>' in html


# ---- HealthSummary: headline, ratio bar, counts (issue 110) ----


def test_the_headline_counts_match_the_health_counts(html: str) -> None:
    datasets = json.loads((FIXTURES / "datasets.json").read_text(encoding="utf-8"))
    total = len(datasets)
    problems = sum(1 for d in datasets if d["health"] != "healthy")
    assert problems, "fixture has no problem dataset to check the headline against"
    assert f'<p class="health-headline">{total}개 중 {problems}개에 문제가 있습니다.</p>' in html


def test_a_zero_problem_snapshot_gets_its_own_headline(build_demo: ModuleType) -> None:
    datasets = json.loads((FIXTURES / "datasets.json").read_text(encoding="utf-8"))
    for row in datasets:
        row["health"] = "healthy"
        row["active_incident_ids"] = []
        for check in row["checks"].values():
            check["status"] = "pass"
            check["summary"] = None
    changes = json.loads((FIXTURES / "changes.json").read_text(encoding="utf-8"))
    for change in changes:
        change["related_incident_id"] = None
    html = build_demo.render(_all_healthy_fixtures(datasets, changes))
    assert '<p class="health-headline">15개 모두 정상입니다.</p>' in html
    assert "문제가 있습니다" not in html


def test_the_status_ratio_bar_is_decorative_and_sums_to_the_counts(html: str) -> None:
    summary = html[
        html.index('class="summary"') : html.index("</section>", html.index('class="summary"'))
    ]
    assert '<div class="status-ratio-bar" aria-hidden="true">' in summary
    widths = [int(w) for w in re.findall(r'style="width: (\d+)%"', summary)]
    assert widths and sum(widths) == 100
    assert len(widths) <= 4


# ---- CheckMatrix: every check state, including not_applicable (issue 110) ----


def test_the_matrix_renders_every_check_state_including_not_applicable(
    build_demo: ModuleType,
) -> None:
    # The preview shows only 6 rows (PREVIEW_SIZE); the full list, as the matrix
    # shows once the catalog page does not exist yet, has every check state.
    full = build_demo.render(built_pages=build_demo.BUILT_PAGES - {"datasets"})
    matrix = panel(full, "Datasets")
    for status in ("pass", "warn", "fail", "unknown", "not_applicable"):
        assert f'class="check-cell check-cell-{status}"' in matrix
    assert 'aria-label="Freshness: Not applicable' in matrix


def test_the_matrix_has_an_accessible_checks_column_header(html: str) -> None:
    matrix = panel(html, "Datasets")
    assert (
        '<th scope="col" aria-label="Checks (Availability, Freshness, Contract, '
        'Quality)">Checks</th>' in matrix
    )


def _all_healthy_fixtures(datasets: list, changes: list) -> Path:
    import tempfile

    directory = Path(tempfile.mkdtemp()) / "fixtures"
    directory.mkdir()
    for name in ("snapshot", "histories"):
        (directory / f"{name}.json").write_text(
            (FIXTURES / f"{name}.json").read_text(encoding="utf-8"), encoding="utf-8"
        )
    (directory / "datasets.json").write_text(json.dumps(datasets), encoding="utf-8")
    (directory / "changes.json").write_text(json.dumps(changes), encoding="utf-8")
    (directory / "incidents.json").write_text("[]", encoding="utf-8")
    return directory


def test_issues_come_before_healthy_datasets(build_demo: ModuleType) -> None:
    html = build_demo.render(built_pages=build_demo.BUILT_PAGES - {"datasets"})
    datasets = html.index(">Datasets</h2>")
    assert html.index(">Active Issues</h2>") < html.index("Healthy</span>", datasets)
    rows = re.findall(r'<span class="status-badge status-(\w+)">', html[datasets:])
    rank = ["critical", "degraded", "unknown", "healthy"]
    assert rows == sorted(rows, key=rank.index)


def test_changes_look_different_from_incidents(html: str) -> None:
    changes = panel(html, "Recent Changes")
    assert 'class="change-row"' in changes
    assert 'class="change-badge"' in changes
    assert "status-badge" not in changes
    assert "물품목록정보" in changes and "productEngName" in changes


def test_without_a_catalog_the_overview_keeps_every_dataset(build_demo: ModuleType) -> None:
    page = build_demo.render(built_pages=build_demo.BUILT_PAGES - {"datasets"})
    datasets = panel(page, "Datasets")
    assert len(re.findall(r"<tbody>.*?</tbody>", datasets, re.DOTALL)) == 1
    assert len(re.findall(r'<span class="status-badge status-\w+">', datasets)) == 15
    assert "View all datasets" not in datasets


def test_with_a_catalog_the_overview_previews_and_links_to_it(build_demo: ModuleType) -> None:
    page = build_demo.render()
    datasets = panel(page, "Datasets")
    rows = re.findall(r'<span class="status-badge status-(\w+)">', datasets)
    assert len(rows) == build_demo.PREVIEW_SIZE < 15
    assert rows[0] == "critical"
    assert '<a class="view-all" href="datasets/">View all datasets</a>' in datasets


def test_an_empty_issue_list_says_so(build_demo: ModuleType, tmp_path: Path) -> None:
    directory = tmp_path / "fixtures"
    directory.mkdir()
    for name in ("snapshot", "datasets", "changes", "histories"):
        (directory / f"{name}.json").write_text(
            (FIXTURES / f"{name}.json").read_text(encoding="utf-8"), encoding="utf-8"
        )
    datasets = json.loads((FIXTURES / "datasets.json").read_text(encoding="utf-8"))
    for row in datasets:
        row["active_incident_ids"] = []
    changes = json.loads((FIXTURES / "changes.json").read_text(encoding="utf-8"))
    for change in changes:
        change["related_incident_id"] = None
    (directory / "datasets.json").write_text(json.dumps(datasets), encoding="utf-8")
    (directory / "changes.json").write_text(json.dumps(changes), encoding="utf-8")
    (directory / "incidents.json").write_text("[]", encoding="utf-8")
    issues = panel(build_demo.render(directory), "Active Issues")
    assert '<p class="empty-state">' in issues
    assert '<span class="panel-count">0</span>' in issues


@pytest.mark.parametrize(
    ("minutes", "text"), [(0, "0m"), (29, "29m"), (60, "1h 0m"), (75, "1h 15m"), (1500, "1d 1h")]
)
def test_duration_is_short_and_readable(minutes: int, text: str) -> None:
    from datetime import UTC, datetime, timedelta

    start = datetime(2026, 10, 2, tzinfo=UTC)
    assert duration(start, start + timedelta(minutes=minutes)) == text
