"""The public read models carry every product surface, and the fixtures obey them (#82).

`kpubdata_watch.api.read_models.public` defines what the read API returns and
what the templates render: dataset summaries and details, check results,
incidents with their evidence, changes with their diff, and 30-day history.
`ProductSnapshot` loads the fixture demo's five files into those models and
rejects any reference that does not resolve.
"""

from __future__ import annotations

import copy
import json
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from kpubdata_watch.api.read_models.public import CHECK_NAMES, HISTORY_DAYS
from kpubdata_watch.api.read_models.snapshot import FIXTURE_FILES, ProductSnapshot

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES = REPO_ROOT / "demo" / "fixtures"

# A relative time, in English or Korean, goes stale the moment a static page is built.
RELATIVE_TIME = re.compile(r"\bago\b|분 전|시간 전|일 전", re.IGNORECASE)


@pytest.fixture(scope="module")
def snapshot() -> ProductSnapshot:
    return ProductSnapshot.from_directory(FIXTURES)


def _raw() -> dict[str, Any]:
    return {
        name: json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
        for name in FIXTURE_FILES
    }


def test_the_fixture_is_split_into_the_five_product_files() -> None:
    assert FIXTURE_FILES == ("snapshot", "datasets", "incidents", "changes", "histories")
    for name in FIXTURE_FILES:
        assert (FIXTURES / f"{name}.json").is_file()


def test_every_dataset_reports_all_four_checks_with_a_status(snapshot: ProductSnapshot) -> None:
    assert CHECK_NAMES == ("availability", "freshness", "contract", "quality")
    for dataset in snapshot.datasets:
        for name in CHECK_NAMES:
            check = getattr(dataset.checks, name)
            assert check.status in {"pass", "warn", "fail", "unknown", "not_applicable"}


def test_a_dataset_detail_resolves_its_incidents_and_changes(snapshot: ProductSnapshot) -> None:
    detail = snapshot.dataset_detail("datago.apt_rent")
    assert detail.provider.name == "국토교통부"
    assert detail.health == "critical"
    assert detail.checks.contract.status == "fail"
    assert [incident.id for incident in detail.active_incidents] == ["inc-contract-apt-rent-001"]
    assert [change.id for change in detail.latest_changes] == ["chg-contract-apt-rent-001"]
    assert detail.last_healthy_at < detail.last_checked_at


def test_incident_evidence_explains_the_detection(snapshot: ProductSnapshot) -> None:
    for incident in snapshot.incidents:
        evidence = incident.evidence
        assert evidence.expected and evidence.observed and evidence.difference
        assert evidence.rule.id and evidence.rule.description
        assert incident.started_at <= incident.detected_at


def test_a_resolved_incident_has_its_whole_lifecycle(snapshot: ProductSnapshot) -> None:
    resolved = [incident for incident in snapshot.incidents if incident.status == "resolved"]
    assert resolved, "the fixture should show one resolved incident"
    for incident in resolved:
        assert incident.confirmed_at is not None and incident.resolved_at is not None
        assert incident.detected_at <= incident.confirmed_at <= incident.resolved_at


def test_changes_carry_a_readable_diff_and_their_health_impact(snapshot: ProductSnapshot) -> None:
    additive = snapshot.change("chg-contract-pps-001")
    assert additive.diff.added == ["productEngName:string"]
    assert additive.health_impact == "none"
    assert additive.related_incident_id is None
    breaking = snapshot.change("chg-contract-apt-rent-001")
    assert breaking.diff.removed == ["addr2:string"]
    assert breaking.health_impact == "critical"
    assert breaking.related_incident_id == "inc-contract-apt-rent-001"


def test_every_dataset_has_thirty_consecutive_days_of_history(snapshot: ProductSnapshot) -> None:
    last_day = snapshot.generated_at.date()
    for dataset in snapshot.datasets:
        history = snapshot.history(dataset.id)
        days = [day.date for day in history.days]
        assert len(days) == HISTORY_DAYS == 30
        assert days == [last_day - timedelta(days=offset) for offset in range(29, -1, -1)]
        assert history.days[-1].health == dataset.health


def test_every_timestamp_is_timezone_aware(snapshot: ProductSnapshot) -> None:
    assert snapshot.generated_at.utcoffset() is not None
    for dataset in snapshot.datasets:
        assert dataset.last_checked_at.utcoffset() is not None
    for incident in snapshot.incidents:
        assert incident.detected_at.utcoffset() is not None
    for change in snapshot.changes:
        assert change.detected_at.utcoffset() is not None


def test_the_fixture_stores_no_relative_time() -> None:
    def walk(value: Any, where: str) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                assert not key.endswith("_label"), f"{where}.{key}: store a timestamp, not a label"
                walk(item, f"{where}.{key}")
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, f"{where}[{index}]")
        elif isinstance(value, str):
            assert not RELATIVE_TIME.search(value), f"{where}: {value!r} is a relative time"

    for name, content in _raw().items():
        walk(content, name)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (
            lambda raw: raw["datasets"][0]["active_incident_ids"].append("inc-missing"),
            "inc-missing",
        ),
        (
            lambda raw: raw["datasets"][0]["latest_change_ids"].append("chg-missing"),
            "chg-missing",
        ),
        (lambda raw: raw["incidents"][0].update(dataset_id="no.such.dataset"), "no.such.dataset"),
        (lambda raw: raw["changes"][0].update(related_incident_id="inc-missing"), "inc-missing"),
        (lambda raw: raw["histories"][0].update(dataset_id="no.such.dataset"), "no.such.dataset"),
        (lambda raw: raw["histories"].pop(), "has no history"),
        (lambda raw: raw["datasets"].append(copy.deepcopy(raw["datasets"][0])), "duplicate"),
    ],
)
def test_a_reference_that_does_not_resolve_is_rejected(change: Any, message: str) -> None:
    raw = _raw()
    change(raw)
    with pytest.raises(ValidationError, match=re.escape(message)):
        ProductSnapshot.model_validate(raw)


def test_an_active_incident_must_belong_to_its_dataset() -> None:
    raw = _raw()
    rent = next(row for row in raw["datasets"] if row["id"] == "datago.apt_rent")
    bike = next(row for row in raw["datasets"] if row["id"] == "seoul.public_bike")
    rent["active_incident_ids"] = list(bike["active_incident_ids"])
    with pytest.raises(ValidationError, match="belongs to seoul.public_bike"):
        ProductSnapshot.model_validate(raw)


def test_history_dates_are_parsed_as_dates(snapshot: ProductSnapshot) -> None:
    assert isinstance(snapshot.history("datago.apt_rent").days[0].date, date)
