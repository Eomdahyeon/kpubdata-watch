"""History answers "how reliable has this been" over the last 30 days (#109, ADR 0013).

Overview and History are symmetric: the same dataset rows, different columns.
These tests check the page's three derived views — the daily abnormal-count
bar, the dataset x 30-day heatmap and the date-grouped incident/change
timeline — and that the numbers they show trace back to the fixtures rather
than to a number written into this file.
"""

from __future__ import annotations

import importlib.util
import json
import re
from itertools import groupby
from pathlib import Path
from types import ModuleType

import pytest

from kpubdata_watch.api.read_models.public import HISTORY_DAYS
from kpubdata_watch.api.read_models.snapshot import ProductSnapshot
from kpubdata_watch.web.presentation import NAV_ITEMS

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "build_demo.py"
FIXTURES = REPO_ROOT / "demo" / "fixtures"
_HEALTH_RANK = {"critical": 0, "degraded": 1, "unknown": 2, "healthy": 3}


@pytest.fixture(scope="module")
def build_demo() -> ModuleType:
    spec = importlib.util.spec_from_file_location("build_demo", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def snapshot() -> ProductSnapshot:
    return ProductSnapshot.from_directory(FIXTURES)


@pytest.fixture(scope="module")
def ctx(build_demo: ModuleType, snapshot: ProductSnapshot) -> dict:
    return build_demo.history_context(snapshot)


@pytest.fixture(scope="module")
def html(build_demo: ModuleType, snapshot: ProductSnapshot) -> str:
    rendered: str = build_demo.render_history(snapshot)
    return rendered


def panel(html: str, heading: str) -> str:
    start = html.index(f">{heading}</h2>")
    return html[start : html.find("</section>", start)]


# ---- Nav ----


def test_history_is_in_the_navigation_right_after_overview() -> None:
    keys = [key for key, _, _ in NAV_ITEMS]
    assert "history" in keys
    assert keys.index("history") == keys.index("overview") + 1
    assert dict((key, label) for key, label, _ in NAV_ITEMS)["history"] == "History"


def test_the_current_page_is_marked_history(html: str) -> None:
    assert '<a class="nav-item" href="../history/" aria-current="page">History</a>' in html


# ---- Heatmap: one row per dataset, HISTORY_DAYS cells each ----


def test_heatmap_has_one_row_per_dataset_and_history_days_cells(ctx: dict) -> None:
    datasets = json.loads((FIXTURES / "datasets.json").read_text(encoding="utf-8"))
    rows = ctx["heatmap_rows"]
    assert len(rows) == len(datasets)
    assert all(len(row["cells"]) == HISTORY_DAYS for row in rows)


def test_heatmap_sorts_by_abnormal_days_desc_then_current_severity(ctx: dict) -> None:
    rows = ctx["heatmap_rows"]
    abnormal = [row["abnormal_days"] for row in rows]
    assert abnormal == sorted(abnormal, reverse=True)
    for _, group in groupby(rows, key=lambda row: row["abnormal_days"]):
        ranks = [_HEALTH_RANK[row["health"]] for row in group]
        assert ranks == sorted(ranks)
    # The fixture ties two Critical and two Degraded datasets at 1 abnormal day
    # each; Critical must come first within that tie.
    tied = [row for row in rows if row["abnormal_days"] == 1]
    assert len(tied) >= 2
    assert tied[0]["health"] == "critical"


def test_heatmap_cell_has_a_date_and_health_label(html: str) -> None:
    grid = panel(html, "Dataset History")
    label = "2026-09-21 Degraded"
    assert f'title="{label}"' in grid or re.search(r'aria-label="2026-\d\d-\d\d \w+"', grid)
    assert re.search(r'aria-label="2026-\d\d-\d\d \w+"', grid)


def test_heatmap_row_shows_the_abnormal_day_count_and_links_the_dataset(html: str) -> None:
    grid = panel(html, "Dataset History")
    assert "비정상 3일" in grid  # datago.underground_safety: 3 Degraded days
    assert 'href="../datasets/datago.underground_safety/"' in grid


def test_heatmap_screen_reader_summary_is_present(html: str) -> None:
    grid = panel(html, "Dataset History")
    assert "비정상인 날이 있었던 데이터셋은" in grid


# ---- Daily bar: 30 days, degraded/critical/unknown only ----


def test_daily_counts_has_one_entry_per_history_day(ctx: dict) -> None:
    assert len(ctx["daily_counts"]) == HISTORY_DAYS


def test_daily_totals_match_the_fixture_history(ctx: dict) -> None:
    from_context = sum(day["total"] for day in ctx["daily_counts"])
    from_rows = sum(row["abnormal_days"] for row in ctx["heatmap_rows"])
    raw = sum(
        1
        for history in json.loads((FIXTURES / "histories.json").read_text(encoding="utf-8"))
        for day in history["days"]
        if day["health"] != "healthy"
    )
    assert from_context == from_rows == raw


def test_daily_bar_only_stacks_abnormal_tones(ctx: dict) -> None:
    for day in ctx["daily_counts"]:
        assert set(day["heights"]) == {"degraded", "critical", "unknown"}
        assert "healthy" not in day


def test_daily_bar_renders_a_segment_per_day_and_sr_summary(html: str) -> None:
    bar = panel(html, "Daily Abnormal Datasets")
    assert bar.count('class="daily-bar-day"') == HISTORY_DAYS
    assert "경우는 총" in bar


# ---- Timeline: date-grouped, newest first, resolved incidents show duration ----


def test_timeline_is_grouped_by_date_newest_first(html: str) -> None:
    section = panel(html, "Incidents and Changes")
    dates = re.findall(r'<h3 class="timeline-date">([\d-]+)</h3>', section)
    assert dates == sorted(dates, reverse=True)
    assert len(dates) == len(set(dates))


def test_a_resolved_incident_shows_its_duration(html: str) -> None:
    incidents = json.loads((FIXTURES / "incidents.json").read_text(encoding="utf-8"))
    resolved = [i for i in incidents if i["status"] == "resolved"]
    assert resolved, "fixture has no resolved incident to check against"
    section = panel(html, "Incidents and Changes")
    assert "1h 9m" in section  # inc-freshness-bus-001: 08:12 -> 09:21


def test_timeline_links_to_incident_and_change_detail_pages(html: str) -> None:
    section = panel(html, "Incidents and Changes")
    assert 'href="../incidents/inc-freshness-bus-001/"' in section
    assert 'href="../changes/chg-contract-apt-rent-001/"' in section


# ---- Build & broken links ----


def test_build_has_no_broken_internal_links(build_demo: ModuleType, tmp_path: Path) -> None:
    out = build_demo.build(output_dir=tmp_path / "_site")
    assert build_demo.broken_links(out) == []
    assert (out / "history" / "index.html").is_file()
