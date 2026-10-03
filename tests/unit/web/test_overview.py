"""The Overview answers "what is wrong right now?" first (#84).

Order: page header, Health summary, Active Issues, Recent Changes, then a
dataset preview. Critical issues come before Degraded ones and every issue is
above the healthy datasets. A Change looks different from an Incident. When
there is no active issue the panel says so. The preview shows part of the
list and links to the full catalog once that page exists; until then the
Overview keeps every dataset so nothing is hidden.
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


def test_the_issue_count_matches_the_active_incidents(html: str) -> None:
    incidents = json.loads((FIXTURES / "incidents.json").read_text(encoding="utf-8"))
    active = [i for i in incidents if i["status"] in {"open", "ongoing"}]
    issues = panel(html, "Active Issues")
    assert len(re.findall(r'<li class="issue-row ', issues)) == len(active)
    assert f'<span class="panel-count">{len(active)}</span>' in html


def test_issues_come_before_healthy_datasets(html: str) -> None:
    assert html.index(">Active Issues</h2>") < html.index(
        "Healthy</span>", html.index(">Datasets</h2>")
    )


def test_changes_look_different_from_incidents(html: str) -> None:
    changes = panel(html, "Recent Changes")
    assert 'class="change-row"' in changes
    assert 'class="change-badge"' in changes
    assert "status-badge" not in changes
    assert "물품목록정보" in changes and "productEngName" in changes


def test_without_a_catalog_the_overview_keeps_every_dataset(html: str) -> None:
    datasets = panel(html, "Datasets")
    assert len(re.findall(r'<li class="dataset-row ', datasets)) == 15
    assert "View all datasets" not in datasets


def test_with_a_catalog_the_overview_previews_and_links_to_it(build_demo: ModuleType) -> None:
    built = build_demo.BUILT_PAGES | {"datasets"}
    page = build_demo.render(built_pages=built)
    datasets = panel(page, "Datasets")
    rows = re.findall(r'<li class="dataset-row status-(\w+)"', datasets)
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
