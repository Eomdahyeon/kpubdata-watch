"""Evidence mini charts render only what one detection's evidence has (#111).

`evidence_view` turns `incident.check` plus the evidence keys actually present
into a template-ready dict for `evidence_chart` (ADR 0013 (b)): a quality/volume
band and dot, a freshness time axis (two shapes: an expected window, or an
allowed-age bar), availability's failure bars, or contract's added/removed
chips. An unmatched shape, or a required key missing or the wrong type for a
shape it did match, returns `None` instead of guessing -- the caller keeps the
existing Expected/Observed/Difference/Rule table either way.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from kpubdata_watch.api.read_models.public import Incident
from kpubdata_watch.api.read_models.snapshot import ProductSnapshot
from kpubdata_watch.web.presentation import evidence_view

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES = REPO_ROOT / "demo" / "fixtures"


@pytest.fixture(scope="module")
def snapshot() -> ProductSnapshot:
    return ProductSnapshot.from_directory(FIXTURES)


def _incident(snapshot: ProductSnapshot, incident_id: str) -> Incident:
    return snapshot.incident(incident_id)


# ---- one evidence_view result per shape present in demo/fixtures/incidents.json ----


def test_quality_volume_draws_the_band_the_dot_and_a_signed_percent(
    snapshot: ProductSnapshot,
) -> None:
    view = evidence_view(_incident(snapshot, "inc-volume-kostat-001"), snapshot.generated_at)
    assert view is not None
    assert view["kind"] == "quality_volume"
    assert view["percent_label"] == "−40%"  # 6,000 is 40% under the 10,000 minimum
    assert view["dot_tone"] == "degraded"  # the incident's own severity (warning)
    assert 0 <= view["dot_x"] <= 290
    assert view["band_width"] > 0


def test_freshness_window_draws_the_window_latest_data_snapshot_and_delay(
    snapshot: ProductSnapshot,
) -> None:
    view = evidence_view(
        _incident(snapshot, "inc-freshness-underground-001"), snapshot.generated_at
    )
    assert view is not None
    assert view["kind"] == "freshness_window"
    assert view["window_width"] > 0
    # The window (20:00 +/- 30min) closed at 20:30; the snapshot is at 21:15, so a
    # delay segment is drawn.
    assert view["delay_width"] > 0
    assert "2026-10-02 20:00 KST" in view["caption"]
    assert "2026-10-02 18:48 KST" in view["caption"]


def test_a_resolved_freshness_window_incident_still_gets_a_view(
    snapshot: ProductSnapshot,
) -> None:
    view = evidence_view(_incident(snapshot, "inc-freshness-bus-001"), snapshot.generated_at)
    assert view is not None
    assert view["kind"] == "freshness_window"


def test_freshness_age_compares_allowed_and_current_age_against_the_snapshot(
    snapshot: ProductSnapshot,
) -> None:
    view = evidence_view(_incident(snapshot, "inc-freshness-bus-002"), snapshot.generated_at)
    assert view is not None
    assert view["kind"] == "freshness_age"
    # Snapshot 21:15 minus latest data 20:31 is 44 minutes old, against a 10 minute
    # allowance -- computed from generated_at, never wall clock.
    assert view["over"] is True
    assert view["current_width"] > view["allowed_width"]
    assert "44m" in view["caption"]
    assert "10m" in view["caption"]


def test_availability_draws_one_bar_per_failure_and_last_success_as_text_only(
    snapshot: ProductSnapshot,
) -> None:
    view = evidence_view(_incident(snapshot, "inc-availability-bike-001"), snapshot.generated_at)
    assert view is not None
    assert view["kind"] == "availability"
    # Exactly 3 bars, one per consecutive_failures -- no extra mark for a probe
    # the evidence does not record.
    assert len(view["bars"]) == 3
    assert view["last_success_label"] == "2026-10-02 20:43 KST"


def test_contract_splits_expected_and_observed_fields_into_added_and_removed(
    snapshot: ProductSnapshot,
) -> None:
    view = evidence_view(_incident(snapshot, "inc-contract-apt-rent-001"), snapshot.generated_at)
    assert view is not None
    assert view["kind"] == "contract"
    assert view["removed"] == ["addr2:string"]
    assert view["added"] == []


# ---- fallback: an evidence shape evidence_view does not recognise ----


GENERATED_AT = datetime(2026, 10, 2, 12, 15, tzinfo=UTC)


def _incident_with(check: str, expected: dict, observed: dict) -> Incident:
    return Incident.model_validate(
        {
            "id": "inc-test",
            "dataset_id": "ds.test",
            "check": check,
            "severity": "warning",
            "status": "ongoing",
            "title": "Test incident",
            "summary": "Test summary",
            "started_at": "2026-10-02T10:00:00+09:00",
            "detected_at": "2026-10-02T10:00:00+09:00",
            "evidence": {
                "expected": expected,
                "observed": observed,
                "difference": {},
                "rule": {"id": "test.rule", "description": "Test rule"},
                "first_seen_at": "2026-10-02T10:00:00+09:00",
            },
            "timeline": [],
        }
    )


def test_an_unmatched_evidence_shape_falls_back_to_none() -> None:
    incident = _incident_with(
        "quality", {"something_unrecognised": 1}, {"something_unrecognised": 2}
    )
    assert evidence_view(incident, GENERATED_AT) is None


# ---- malformed: the shape matched by `check`, but a required value is unusable ----


@pytest.mark.parametrize(
    ("check", "expected", "observed"),
    [
        # A reversed band (min above max) cannot place the observed dot.
        ("quality", {"record_count_min": 500, "record_count_max": 100}, {"record_count": 50}),
        # http_status as a string, not a number.
        (
            "availability",
            {"http_status": "200"},
            {"http_status": 500, "consecutive_failures": 3},
        ),
        # latest_data_at is not a parseable, timezone-aware timestamp.
        ("freshness", {"max_age_minutes": 10}, {"latest_data_at": "not-a-time"}),
    ],
)
def test_malformed_evidence_returns_none_instead_of_guessing(
    check: str, expected: dict, observed: dict
) -> None:
    assert evidence_view(_incident_with(check, expected, observed), GENERATED_AT) is None
