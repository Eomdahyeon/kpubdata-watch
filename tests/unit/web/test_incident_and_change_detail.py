"""Incident and Change detail pages explain a detection with its evidence (#87).

An Incident page shows its lifecycle and answers "Why was this detected?" with
Expected, Observed, Difference and Rule, then the observation timeline and the
related change; the raw evidence is available but folded away. A Change page
shows a human-readable diff first, when it was first observed, what it did to
Health and the related incident. An additive change never looks like an outage.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
from types import ModuleType

import pytest

from kpubdata_watch.web.presentation import evidence_value

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "build_demo.py"
FIXTURES = REPO_ROOT / "demo" / "fixtures"
LINK_ATTR = re.compile(r'(?:href|src)="([^"]+)"')


@pytest.fixture(scope="module")
def site(tmp_path_factory: pytest.TempPathFactory) -> Path:
    spec = importlib.util.spec_from_file_location("build_demo", SCRIPT)
    assert spec is not None and spec.loader is not None
    module: ModuleType = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    out: Path = module.build(output_dir=tmp_path_factory.mktemp("site") / "_site")
    return out


def read(site: Path, kind: str, identifier: str) -> str:
    return (site / kind / identifier / "index.html").read_text(encoding="utf-8")


def section(html: str, heading: str) -> str:
    start = html.index(f">{heading}</h2>")
    return html[start : html.find("</section>", start)]


def test_every_incident_and_change_gets_a_page(site: Path) -> None:
    for kind, name in (("incidents", "incidents"), ("changes", "changes")):
        expected = {row["id"] for row in json.loads((FIXTURES / f"{name}.json").read_text())}
        built = {path.parent.name for path in (site / kind).glob("*/index.html")}
        assert built == expected


def test_the_incident_explains_why_it_was_detected(site: Path) -> None:
    why = section(read(site, "incidents", "inc-availability-bike-001"), "Why was this detected?")
    for label in ("Expected", "Observed", "Difference", "Rule"):
        assert f"<dt>{label}</dt>" in why
    assert "http_status: 200" in why
    assert "http_status: 500" in why and "consecutive_failures: 3" in why
    assert "Three consecutive failed probes" in why


def test_a_resolved_incident_shows_its_whole_lifecycle(site: Path) -> None:
    lifecycle = section(read(site, "incidents", "inc-freshness-bus-001"), "Lifecycle")
    for label in ("Started", "Detected", "Confirmed", "Resolved", "Duration"):
        assert f"<dt>{label}</dt>" in lifecycle
    assert "2026-10-01 09:21 KST" in lifecycle
    assert "1h 9m" in lifecycle


def test_the_raw_evidence_is_secondary(site: Path) -> None:
    html = read(site, "incidents", "inc-contract-apt-rent-001")
    why = html.index(">Why was this detected?</h2>")
    raw = html.index('<details class="raw-evidence">')
    assert why < raw
    assert "<summary>View raw evidence</summary>" in html


def test_the_evidence_chart_sits_above_the_expected_observed_table(site: Path) -> None:
    """The mini chart and the text table both render; the chart comes first (#111)."""
    why = section(read(site, "incidents", "inc-availability-bike-001"), "Why was this detected?")
    chart = why.index('<div class="evidence-chart">')
    table = why.index('<dl class="metadata evidence">')
    assert chart < table
    assert 'role="img"' in why
    assert "<title>" in why
    assert "<dt>Expected</dt>" in why and "<dt>Observed</dt>" in why


def test_the_contract_incident_chart_reuses_the_contract_diff_chips(site: Path) -> None:
    why = section(read(site, "incidents", "inc-contract-apt-rent-001"), "Why was this detected?")
    chart = why.index('<div class="evidence-chart">')
    table = why.index('<dl class="metadata evidence">')
    assert chart < table
    # Once inside the evidence chart (above the table) and once more for the
    # related change's own ContractDiff further down the same panel.
    assert why.count('<li class="diff-removed">') == 2
    assert why.index('<div class="evidence-chart">') < why.index('<ul class="contract-diff">')


def test_the_timeline_and_related_change_are_shown(site: Path) -> None:
    html = read(site, "incidents", "inc-contract-apt-rent-001")
    timeline = section(html, "Observation Timeline")
    assert "필드 addr2 삭제 관측" in timeline
    assert 'href="../../changes/chg-contract-apt-rent-001/"' in html


def test_an_additive_change_does_not_look_like_an_outage(site: Path) -> None:
    html = read(site, "changes", "chg-contract-pps-001")
    diff = section(html, "Contract Diff")
    assert '<li class="diff-added">' in diff and "productEngName:string" in diff
    impact = section(html, "Health Impact")
    assert "None" in impact and "Healthy" in impact
    assert "status-critical" not in html and "status-degraded" not in html


def test_a_breaking_change_links_its_incident(site: Path) -> None:
    html = read(site, "changes", "chg-contract-apt-rent-001")
    assert '<li class="diff-removed">' in section(html, "Contract Diff")
    impact = section(html, "Health Impact")
    assert 'class="status-badge status-critical"' in impact
    assert 'href="../../incidents/inc-contract-apt-rent-001/"' in impact


def test_dataset_and_overview_pages_now_link_to_incidents_and_changes(site: Path) -> None:
    dataset = read(site, "datasets", "datago.apt_rent")
    assert 'href="../../incidents/inc-contract-apt-rent-001/"' in dataset
    assert 'href="../../changes/chg-contract-apt-rent-001/"' in dataset
    overview = (site / "index.html").read_text(encoding="utf-8")
    assert 'href="incidents/inc-availability-bike-001/"' in overview
    assert 'href="changes/chg-contract-pps-001/"' in overview


def test_every_relative_link_on_every_page_resolves(site: Path) -> None:
    for page in site.rglob("index.html"):
        for target in LINK_ATTR.findall(page.read_text(encoding="utf-8")):
            if target.startswith(("https://", "#")) or target.endswith("docs/"):
                continue
            assert (page.parent / target).resolve().exists(), f"{page}: {target}"


@pytest.mark.parametrize(
    ("value", "text"),
    [
        ("2026-10-02T21:03:00+09:00", "2026-10-02 21:03:00 KST"),
        (["addr2:string"], "addr2:string"),
        (["a", "b"], "a, b"),
        (3, "3"),
        ("plain", "plain"),
    ],
)
def test_evidence_values_are_readable(value: object, text: str) -> None:
    assert evidence_value(value) == text
