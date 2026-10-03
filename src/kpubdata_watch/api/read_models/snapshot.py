"""A complete set of public read models at one moment, with its references checked (#82).

The fixture demo stores one snapshot as five JSON files (`FIXTURE_FILES`) under
`demo/fixtures/`. Loading them through `ProductSnapshot` rejects every
reference that does not resolve: a dataset pointing at a missing incident or
change, an incident or change for a dataset that does not exist, an active
incident filed under the wrong dataset, a history for an unknown dataset, or a
dataset without history. A page built from a snapshot therefore never links to
nothing.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable
from datetime import timedelta
from pathlib import Path
from typing import Any, Self

from pydantic import AwareDatetime, model_validator

from kpubdata_watch.api.read_models.public import (
    HISTORY_DAYS,
    Change,
    ChangeSummary,
    DatasetDetail,
    DatasetHistory,
    DatasetRecord,
    Incident,
    IncidentSummary,
    ReadModel,
)

FIXTURE_FILES = ("snapshot", "datasets", "incidents", "changes", "histories")
ACTIVE_INCIDENT_STATUSES = frozenset({"open", "ongoing"})


def _duplicates(ids: Iterable[str]) -> list[str]:
    return sorted(key for key, count in Counter(ids).items() if count > 1)


class ProductSnapshot(ReadModel):
    generated_at: AwareDatetime
    datasets: list[DatasetRecord]
    incidents: list[Incident]
    changes: list[Change]
    histories: list[DatasetHistory]

    @classmethod
    def from_directory(cls, directory: Path) -> ProductSnapshot:
        """Load the five fixture files from `directory`."""
        raw: dict[str, Any] = {
            name: json.loads((directory / f"{name}.json").read_text(encoding="utf-8"))
            for name in FIXTURE_FILES
        }
        return cls.model_validate(raw)

    @model_validator(mode="before")
    @classmethod
    def _unwrap_snapshot_file(cls, data: Any) -> Any:
        # snapshot.json holds `{"generated_at": ...}`; lift it to the top level.
        if isinstance(data, dict) and isinstance(data.get("snapshot"), dict):
            data = {**data}
            data["generated_at"] = data.pop("snapshot")["generated_at"]
        return data

    @model_validator(mode="after")
    def _references_resolve(self) -> Self:
        problems: list[str] = []
        for kind, ids in (
            ("dataset", [d.id for d in self.datasets]),
            ("incident", [i.id for i in self.incidents]),
            ("change", [c.id for c in self.changes]),
            ("history", [h.dataset_id for h in self.histories]),
        ):
            problems.extend(f"duplicate {kind} id {key}" for key in _duplicates(ids))

        datasets = {d.id for d in self.datasets}
        active = {d.id: set(d.active_incident_ids) for d in self.datasets}
        incidents = {i.id: i for i in self.incidents}
        changes = {c.id: c for c in self.changes}
        for dataset in self.datasets:
            for incident_id in dataset.active_incident_ids:
                incident = incidents.get(incident_id)
                if incident is None:
                    problems.append(f"{dataset.id}: unknown incident {incident_id}")
                elif incident.dataset_id != dataset.id:
                    problems.append(
                        f"{dataset.id}: incident {incident_id} belongs to {incident.dataset_id}"
                    )
                elif incident.status not in ACTIVE_INCIDENT_STATUSES:
                    problems.append(
                        f"{dataset.id}: incident {incident_id} is {incident.status}, not active"
                    )
            for change_id in dataset.latest_change_ids:
                change = changes.get(change_id)
                if change is None:
                    problems.append(f"{dataset.id}: unknown change {change_id}")
                elif change.dataset_id != dataset.id:
                    problems.append(
                        f"{dataset.id}: change {change_id} belongs to {change.dataset_id}"
                    )
        for incident in self.incidents:
            if incident.dataset_id not in datasets:
                problems.append(f"incident {incident.id}: unknown dataset {incident.dataset_id}")
            elif (
                incident.status in ACTIVE_INCIDENT_STATUSES
                and incident.id not in active[incident.dataset_id]
            ):
                problems.append(
                    f"{incident.dataset_id}: {incident.status} incident {incident.id} "
                    "is missing from active_incident_ids"
                )
            if incident.related_change_id:
                related_change = changes.get(incident.related_change_id)
                if related_change is None:
                    problems.append(
                        f"incident {incident.id}: unknown change {incident.related_change_id}"
                    )
                elif related_change.related_incident_id != incident.id:
                    problems.append(
                        f"incident {incident.id}: change {related_change.id} does not link back "
                        f"(its related_incident_id is {related_change.related_incident_id})"
                    )
        for change in self.changes:
            if change.dataset_id not in datasets:
                problems.append(f"change {change.id}: unknown dataset {change.dataset_id}")
            if change.related_incident_id:
                related_incident = incidents.get(change.related_incident_id)
                if related_incident is None:
                    problems.append(
                        f"change {change.id}: unknown incident {change.related_incident_id}"
                    )
                elif related_incident.related_change_id != change.id:
                    problems.append(
                        f"change {change.id}: incident {related_incident.id} does not link back "
                        f"(its related_change_id is {related_incident.related_change_id})"
                    )
        with_history = {h.dataset_id for h in self.histories}
        for history in self.histories:
            if history.dataset_id not in datasets:
                problems.append(f"history: unknown dataset {history.dataset_id}")
            problems.extend(self._history_problems(history))
        problems.extend(f"{key} has no history" for key in sorted(datasets - with_history))

        if problems:
            raise ValueError("; ".join(problems))
        return self

    def _history_problems(self, history: DatasetHistory) -> list[str]:
        last = self.generated_at.date()
        expected = [last - timedelta(days=n) for n in range(HISTORY_DAYS - 1, -1, -1)]
        if [day.date for day in history.days] != expected:
            return [
                f"history {history.dataset_id}: expected {HISTORY_DAYS} consecutive days "
                f"ending {last.isoformat()}"
            ]
        return []

    def dataset(self, dataset_id: str) -> DatasetRecord:
        return next(d for d in self.datasets if d.id == dataset_id)

    def incident(self, incident_id: str) -> Incident:
        return next(i for i in self.incidents if i.id == incident_id)

    def change(self, change_id: str) -> Change:
        return next(c for c in self.changes if c.id == change_id)

    def history(self, dataset_id: str) -> DatasetHistory:
        return next(h for h in self.histories if h.dataset_id == dataset_id)

    def dataset_detail(self, dataset_id: str) -> DatasetDetail:
        """Resolve a dataset's references into the `GET /api/v1/datasets/{id}` shape."""
        record = self.dataset(dataset_id)
        fields = record.model_dump(exclude={"active_incident_ids", "latest_change_ids"})
        incident_fields = set(IncidentSummary.model_fields)
        change_fields = set(ChangeSummary.model_fields)
        return DatasetDetail(
            **fields,
            active_incidents=[
                IncidentSummary.model_validate(self.incident(i).model_dump(include=incident_fields))
                for i in record.active_incident_ids
            ],
            latest_changes=[
                ChangeSummary.model_validate(self.change(c).model_dump(include=change_fields))
                for c in record.latest_change_ids
            ],
        )
