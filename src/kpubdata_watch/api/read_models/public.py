"""Public read models: what the read API returns and what the pages render (#82).

One set of models serves the fixture demo, the read API (API_CONTRACT.md) and
the templates, so a page never reads a database table and the demo never needs
a shape the service will not produce. Field meanings follow
docs/DOMAIN_MODEL.md: Health is per dataset, a check result is per check, an
Incident is a problem with a lifecycle and evidence, and a Change is an
immutable observed fact that is not necessarily a problem.

Timestamps are timezone-aware. Nothing here stores a relative time such as
"3m ago": a page computes that from `generated_at` when it is rendered.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict

Health = Literal["healthy", "degraded", "critical", "unknown"]
CheckStatus = Literal["pass", "warn", "fail", "unknown", "not_applicable"]
CheckName = Literal["availability", "freshness", "contract", "quality"]
Severity = Literal["info", "warning", "critical"]
IncidentStatus = Literal["open", "ongoing", "resolved", "false_positive"]
HealthImpact = Literal["none", "degraded", "critical"]

CHECK_NAMES: tuple[CheckName, ...] = ("availability", "freshness", "contract", "quality")
HISTORY_DAYS = 30


class ReadModel(BaseModel):
    """Read models are immutable and reject fields the contract does not define."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class Provider(ReadModel):
    id: str
    name: str


class CheckResult(ReadModel):
    status: CheckStatus
    summary: str | None = None


class Checks(ReadModel):
    availability: CheckResult
    freshness: CheckResult
    contract: CheckResult
    quality: CheckResult


class Rule(ReadModel):
    id: str
    description: str


class Evidence(ReadModel):
    """Why a detection fired: the PRD §22 evidence schema."""

    expected: dict[str, Any]
    observed: dict[str, Any]
    difference: dict[str, Any]
    rule: Rule
    first_seen_at: AwareDatetime
    confirmed_at: AwareDatetime | None = None


class TimelineEvent(ReadModel):
    at: AwareDatetime
    summary: str


class IncidentSummary(ReadModel):
    id: str
    dataset_id: str
    check: CheckName
    severity: Severity
    status: IncidentStatus
    title: str
    summary: str
    started_at: AwareDatetime
    detected_at: AwareDatetime
    confirmed_at: AwareDatetime | None = None
    resolved_at: AwareDatetime | None = None


class Incident(IncidentSummary):
    """An incident detail: its summary plus the evidence and observation timeline."""

    evidence: Evidence
    timeline: list[TimelineEvent]
    related_change_id: str | None = None


class ContractDiff(ReadModel):
    """A schema change in `name:type` form, as a reader sees it."""

    added: list[str] = []
    removed: list[str] = []
    changed: list[str] = []


class ChangeSummary(ReadModel):
    id: str
    dataset_id: str
    change_type: str
    severity: Severity
    title: str
    summary: str
    detected_at: AwareDatetime


class Change(ChangeSummary):
    """A change detail: the human-readable diff and what it did to Health."""

    diff: ContractDiff
    health_impact: HealthImpact
    related_incident_id: str | None = None


class DatasetFields(ReadModel):
    """The fields a dataset row and a dataset detail share."""

    id: str
    name: str
    provider: Provider
    category: str
    health: Health
    checks: Checks
    last_checked_at: AwareDatetime
    last_successful_at: AwareDatetime | None = None
    last_healthy_at: AwareDatetime | None = None
    latest_data_at: AwareDatetime | None = None


class DatasetRecord(DatasetFields):
    """A dataset as stored in the fixture: incidents and changes by reference."""

    active_incident_ids: list[str] = []
    latest_change_ids: list[str] = []


class DatasetDetail(DatasetFields):
    """`GET /api/v1/datasets/{id}`: the dataset with its incidents and changes resolved."""

    active_incidents: list[IncidentSummary]
    latest_changes: list[ChangeSummary]


class HistoryDay(ReadModel):
    date: date
    health: Health
    summary: str | None = None


class DatasetHistory(ReadModel):
    """`GET /api/v1/datasets/{id}/history`: one Health per day, oldest first."""

    dataset_id: str
    requested_days: int = HISTORY_DAYS
    effective_days: int = HISTORY_DAYS
    days: list[HistoryDay]


class Snapshot(ReadModel):
    """When the data behind a page was produced; relative times are computed from it."""

    generated_at: AwareDatetime
