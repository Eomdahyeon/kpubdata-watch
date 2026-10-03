"""Dataset Detail explains why a dataset is in its current Health (#86, PRD §47).

The demo builder writes one page per dataset at `datasets/<id>/`. Each page
shows the current Health with when it was last checked and last healthy, all
four checks with a reason when they are not a plain pass, the active incident
and its contract diff, 30 days of history, recent incidents and changes, and
metadata. Unknown never reads as Critical.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from types import ModuleType

import pytest

from kpubdata_watch.web.presentation import CHECK_META, TEMPLATES_DIR

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "build_demo.py"
LINK_ATTR = re.compile(r'(?:href|src)="([^"]+)"')
HEX_COLOR = re.compile(r"#[0-9a-fA-F]{3,8}\b")


@pytest.fixture(scope="module")
def site(tmp_path_factory: pytest.TempPathFactory) -> Path:
    spec = importlib.util.spec_from_file_location("build_demo", SCRIPT)
    assert spec is not None and spec.loader is not None
    module: ModuleType = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    out: Path = module.build(output_dir=tmp_path_factory.mktemp("site") / "_site")
    return out


def page(site: Path, dataset_id: str) -> str:
    return (site / "datasets" / dataset_id / "index.html").read_text(encoding="utf-8")


def section(html: str, heading: str) -> str:
    start = html.index(f">{heading}</h2>")
    end = html.find("</section>", start)
    return html[start:end]


def test_every_dataset_gets_a_detail_page(site: Path) -> None:
    pages = sorted(path.parent.name for path in (site / "datasets").glob("*/index.html"))
    assert len(pages) == 15
    assert "datago.apt_rent" in pages and "kma.ultra_srt_ncst" in pages


def test_the_header_names_the_dataset_its_provider_and_its_health(site: Path) -> None:
    html = page(site, "datago.apt_rent")
    assert "<h1>아파트 전월세 실거래가</h1>" in html
    assert "국토교통부" in html
    assert '<p class="technical-id">datago.apt_rent</p>' in html
    header = html[
        html.index('<header class="page-header">') : html.index(
            "</header>", html.index('<header class="page-header">')
        )
    ]
    assert 'class="status-badge status-critical"' in header


def test_last_checked_and_last_healthy_are_shown(site: Path) -> None:
    html = page(site, "datago.apt_rent")
    assert "<dt>Last checked</dt>" in html and "2026-10-02 21:14:40 KST" in html
    assert "<dt>Last healthy</dt>" in html and "2026-10-02 20:42:00 KST" in html


def test_all_four_checks_show_a_status_and_the_reason(site: Path) -> None:
    checks = section(page(site, "datago.apt_rent"), "Health Checks")
    for name in ("Availability", "Freshness", "Contract", "Quality"):
        assert f">{name}<" in checks
    assert 'class="check-status check-fail"' in checks
    assert CHECK_META["fail"]["label"] in checks
    assert "필드 1개 삭제 (breaking)" in checks


def test_a_check_that_does_not_apply_says_so(site: Path) -> None:
    checks = section(page(site, "datago.hospital_info"), "Health Checks")
    assert 'class="check-status check-not_applicable"' in checks
    assert CHECK_META["not_applicable"]["label"] in checks


def test_the_current_issue_shows_the_incident_and_its_contract_diff(site: Path) -> None:
    issue = section(page(site, "datago.apt_rent"), "Current Issue")
    assert "Breaking contract change" in issue
    assert "응답에서 필드 addr2가 사라졌습니다." in issue
    assert '<li class="diff-removed">' in issue and "<code>addr2:string</code>" in issue
    assert "21:03 KST" in issue


def test_thirty_days_of_history_end_with_the_current_health(site: Path) -> None:
    history = section(page(site, "datago.apt_rent"), "Last 30 Days")
    days = re.findall(r'<li class="history-day status-(\w+)"', history)
    assert len(days) == 30
    assert days[-1] == "critical"
    assert 'aria-label="2026-10-02 · Critical · Breaking contract change"' in history


def test_unknown_is_not_presented_as_critical(site: Path) -> None:
    html = page(site, "kma.ultra_srt_ncst")
    header = html[html.index('<header class="page-header">') :]
    header = header[: header.index("</header>")]
    assert 'class="status-badge status-unknown"' in header
    assert "status-critical" not in header
    assert "데이터셋 장애가 아님" in html


def test_a_healthy_dataset_has_an_empty_incident_list(site: Path) -> None:
    incidents = section(page(site, "visitkorea-tourism"), "Recent Incidents")
    assert 'class="empty-state"' in incidents


def test_an_informational_change_is_listed_without_a_health_colour(site: Path) -> None:
    changes = section(page(site, "pps.product_list"), "Recent Changes")
    assert "Contract changed" in changes
    assert '<li class="diff-added">' in changes
    assert "status-" not in changes


def test_every_relative_link_on_a_detail_page_resolves(site: Path) -> None:
    detail = site / "datasets" / "datago.apt_rent" / "index.html"
    for target in LINK_ATTR.findall(detail.read_text(encoding="utf-8")):
        if target.startswith(("https://", "#")) or target.endswith("docs/"):
            continue
        assert (detail.parent / target).resolve().exists(), target


def test_the_overview_links_each_dataset_to_its_detail_page(site: Path) -> None:
    overview = (site / "index.html").read_text(encoding="utf-8")
    assert '<a class="dataset-name" href="datasets/datago.apt_rent/">' in overview
    for target in re.findall(r'href="(datasets/[^"]+)"', overview):
        assert (site / target / "index.html").exists(), target


def test_the_detail_template_has_no_raw_hex() -> None:
    assert not HEX_COLOR.search((TEMPLATES_DIR / "dataset_detail.html").read_text(encoding="utf-8"))
