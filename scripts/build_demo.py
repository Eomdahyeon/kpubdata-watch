#!/usr/bin/env python3
"""Render the product pages with fixture data into a static demo site (#78, #88).

GitHub Pages hosts a fixture-based demo of the product, not the live service (see
docs/decisions — the production service stays FastAPI + worker + PostgreSQL and
never runs on Pages). This script renders the templates in
`src/kpubdata_watch/web/templates/` with the product snapshot in `demo/fixtures/`
(five files, loaded through the public read models, #82) into a self-contained
output directory that `.github/workflows/deploy.yml` uploads to Pages:

    index.html                    Overview
    datasets/index.html           dataset catalog
    datasets/<id>/index.html      Dataset Detail
    incidents/index.html          incident list
    incidents/<id>/index.html     Incident Detail
    changes/index.html            change list
    changes/<id>/index.html       Change Detail
    static/                       CSS, script and images

Every link is relative, so the site works under any base path such as
`/kpubdata-watch/`, and the build fails if any internal link points at nothing.
Times are shown as clock times in KST, never as "3m ago": a static page is read long
after it is built.

Usage:
    python scripts/build_demo.py [--output _site] [--fixtures demo/fixtures]
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Any

from kpubdata_watch.api.read_models.public import CHECK_NAMES
from kpubdata_watch.api.read_models.snapshot import ProductSnapshot
from kpubdata_watch.web.presentation import (
    CHANGE_ICON,
    CHECK_LABELS,
    HEALTH_META,
    HEALTH_ORDER,
    STATIC_DIR,
    TEMPLATES_DIR,
    duration,
    environment,
    kst_datetime,
    kst_minute,
    kst_time,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = REPO_ROOT / "demo" / "fixtures"
DEFAULT_OUTPUT = REPO_ROOT / "_site"
# The product pages this demo builds; the navigation links only to these (#83).
BUILT_PAGES = frozenset(
    {"overview", "datasets", "dataset", "incidents", "incident", "changes", "change"}
)
# With a full catalog, the Overview previews this many datasets, issues first (#84).
PREVIEW_SIZE = 6
_HEALTH_RANK = {"critical": 0, "degraded": 1, "unknown": 2, "healthy": 3}
_SEVERITY_RANK = {"critical": 0, "warning": 1, "info": 2}
# A check counts toward the catalog's "Check" filter when it is not a plain pass.
_NOT_PASSING = {"warn", "fail", "unknown"}

# The health vocabulary and the Jinja environment come from the package
# (kpubdata_watch.web.presentation, #73); HEALTH_META, HEALTH_ORDER and
# CHANGE_ICON are re-exported here for the tests and for readers of this script.
__all__ = ["CHANGE_ICON", "HEALTH_META", "HEALTH_ORDER", "build", "render"]


def load_datasets(fixtures_dir: Path = FIXTURES_DIR) -> list[dict[str, Any]]:
    """Load the snapshot and shape one row per dataset for the Public Status page.

    `ProductSnapshot` rejects any reference that does not resolve. A row's issue is
    its first active incident, or, for Unknown, the check that could not run; its
    change is its latest change.
    """
    return dataset_rows(ProductSnapshot.from_directory(fixtures_dir))


def dataset_rows(snapshot: ProductSnapshot) -> list[dict[str, Any]]:
    """Shape one Public Status row per dataset from a loaded snapshot."""
    rows: list[dict[str, Any]] = []
    for dataset in snapshot.datasets:
        issue = None
        if dataset.active_incident_ids:
            incident = snapshot.incident(dataset.active_incident_ids[0])
            check = getattr(dataset.checks, incident.check)
            issue = f"{incident.title} · {check.summary}" if check.summary else incident.title
        elif dataset.health == "unknown":
            issue = next(
                (
                    getattr(dataset.checks, name).summary
                    for name in CHECK_NAMES
                    if getattr(dataset.checks, name).summary
                ),
                None,
            )
        change = (
            snapshot.change(dataset.latest_change_ids[0]).title
            if dataset.latest_change_ids
            else None
        )
        rows.append(
            {
                "dataset_id": dataset.id,
                "name": dataset.name,
                "provider": dataset.provider.name,
                "health": dataset.health,
                "checked_label": f"Checked {kst_time(dataset.last_checked_at)}",
                "checked_at": dataset.last_checked_at.isoformat(),
                "checked_exact": kst_datetime(dataset.last_checked_at),
                "issue": issue,
                "change": change,
            }
        )
    return rows


def health_counts(datasets: list[dict[str, Any]]) -> dict[str, int]:
    """Count datasets per health state, in `HEALTH_ORDER`."""
    counts = dict.fromkeys(HEALTH_ORDER, 0)
    for row in datasets:
        counts[row["health"]] += 1
    return counts


def _shell(snapshot: ProductSnapshot, root: str, active_nav: str) -> dict[str, Any]:
    """The context every page's shell needs (#83)."""
    return {
        "root": root,
        "active_nav": active_nav,
        "built_pages": BUILT_PAGES,
        "snapshot_at": kst_minute(snapshot.generated_at),
    }


def overview_context(snapshot: ProductSnapshot, built_pages: frozenset[str]) -> dict[str, Any]:
    """Active issues, recent changes and the dataset list for the Overview (#84)."""
    datasets = {d.id: d for d in snapshot.datasets}
    active = [i for i in snapshot.incidents if i.status in {"open", "ongoing"}]
    active.sort(key=lambda i: (_SEVERITY_RANK[i.severity], i.detected_at))
    issues = [
        {
            "id": i.id,
            "dataset_id": i.dataset_id,
            "dataset_name": datasets[i.dataset_id].name,
            "health": datasets[i.dataset_id].health,
            "check_label": CHECK_LABELS[i.check],
            "severity": i.severity,
            "title": i.title,
            "summary": i.summary,
            "detected_at": i.detected_at,
            "duration": duration(i.started_at, snapshot.generated_at),
        }
        for i in active
    ]
    changes = [
        {**c.model_dump(), "dataset_name": datasets[c.dataset_id].name}
        for c in sorted(snapshot.changes, key=lambda c: c.detected_at, reverse=True)
    ]
    rows = sorted(dataset_rows(snapshot), key=lambda row: _HEALTH_RANK[row["health"]])
    preview = "datasets" in built_pages
    return {
        "active_issues": issues,
        "recent_changes": changes,
        "datasets": rows[:PREVIEW_SIZE] if preview else rows,
        "preview": preview,
        "counts": health_counts(rows),
        "total": len(rows),
    }


def render(fixtures_dir: Path = FIXTURES_DIR, built_pages: frozenset[str] = BUILT_PAGES) -> str:
    """Render the Overview (Public Status) page to a single HTML string."""
    template = environment(TEMPLATES_DIR).get_template("public_status.html")
    snapshot = ProductSnapshot.from_directory(fixtures_dir)
    shell = _shell(snapshot, root="", active_nav="overview")
    shell["built_pages"] = built_pages
    return template.render(**overview_context(snapshot, built_pages), **shell)


def render_dataset(snapshot: ProductSnapshot, dataset_id: str) -> str:
    """Render one Dataset Detail page (#86); it lives at `datasets/<id>/`."""
    template = environment(TEMPLATES_DIR).get_template("dataset_detail.html")
    newest_first = {"key": lambda item: item.detected_at, "reverse": True}
    incidents = sorted(
        (i for i in snapshot.incidents if i.dataset_id == dataset_id), **newest_first
    )
    changes = sorted((c for c in snapshot.changes if c.dataset_id == dataset_id), **newest_first)
    return template.render(
        dataset=snapshot.dataset_detail(dataset_id),
        incidents=incidents,
        changes=changes,
        changes_by_id={c.id: c for c in snapshot.changes},
        history=snapshot.history(dataset_id),
        **_shell(snapshot, root="../../", active_nav="datasets"),
    )


def render_catalog(snapshot: ProductSnapshot) -> str:
    """Render the dataset catalog (#85); it lives at `datasets/`."""
    rows = []
    for dataset in sorted(
        snapshot.datasets, key=lambda d: (_HEALTH_RANK[d.health], d.provider.name, d.name)
    ):
        failing = [
            name for name in CHECK_NAMES if getattr(dataset.checks, name).status in _NOT_PASSING
        ]
        rows.append(
            {
                "id": dataset.id,
                "name": dataset.name,
                "provider_id": dataset.provider.id,
                "provider_name": dataset.provider.name,
                "health": dataset.health,
                "checks": failing,
                "incident": snapshot.incident(dataset.active_incident_ids[0])
                if dataset.active_incident_ids
                else None,
                "change": snapshot.change(dataset.latest_change_ids[0])
                if dataset.latest_change_ids
                else None,
                "last_checked_at": dataset.last_checked_at,
                "search": f"{dataset.name} {dataset.provider.name} {dataset.id}",
            }
        )
    providers = sorted(
        {(d.provider.id, d.provider.name) for d in snapshot.datasets}, key=lambda p: p[1]
    )
    return (
        environment(TEMPLATES_DIR)
        .get_template("catalog.html")
        .render(
            rows=rows,
            providers=providers,
            total=len(rows),
            **_shell(snapshot, root="../", active_nav="datasets"),
        )
    )


def render_incident(snapshot: ProductSnapshot, incident_id: str) -> str:
    """Render one Incident Detail page (#87); it lives at `incidents/<id>/`."""
    incident = snapshot.incident(incident_id)
    end = incident.resolved_at or snapshot.generated_at
    return (
        environment(TEMPLATES_DIR)
        .get_template("incident_detail.html")
        .render(
            incident=incident,
            dataset=snapshot.dataset(incident.dataset_id),
            change=snapshot.change(incident.related_change_id)
            if incident.related_change_id
            else None,
            duration=duration(incident.started_at, end),
            raw_evidence=json.dumps(
                incident.evidence.model_dump(mode="json"), ensure_ascii=False, indent=2
            ),
            **_shell(snapshot, root="../../", active_nav="incidents"),
        )
    )


def render_change(snapshot: ProductSnapshot, change_id: str) -> str:
    """Render one Change Detail page (#87); it lives at `changes/<id>/`."""
    change = snapshot.change(change_id)
    return (
        environment(TEMPLATES_DIR)
        .get_template("change_detail.html")
        .render(
            change=change,
            dataset=snapshot.dataset(change.dataset_id),
            raw_diff=json.dumps(change.diff.model_dump(mode="json"), ensure_ascii=False, indent=2),
            **_shell(snapshot, root="../../", active_nav="changes"),
        )
    )


def render_incident_list(snapshot: ProductSnapshot) -> str:
    """Render the incident list (#88); it lives at `incidents/`."""
    datasets = {d.id: d for d in snapshot.datasets}
    ongoing = sorted(
        (i for i in snapshot.incidents if i.status in {"open", "ongoing"}),
        key=lambda i: (_SEVERITY_RANK[i.severity], i.detected_at),
    )
    resolved = sorted(
        (i for i in snapshot.incidents if i.status not in {"open", "ongoing"}),
        key=lambda i: i.detected_at,
        reverse=True,
    )
    return (
        environment(TEMPLATES_DIR)
        .get_template("incidents.html")
        .render(
            ongoing=[{"incident": i, "dataset": datasets[i.dataset_id]} for i in ongoing],
            resolved=[{"incident": i, "dataset": datasets[i.dataset_id]} for i in resolved],
            **_shell(snapshot, root="../", active_nav="incidents"),
        )
    )


def render_change_list(snapshot: ProductSnapshot) -> str:
    """Render the change list (#88); it lives at `changes/`."""
    datasets = {d.id: d for d in snapshot.datasets}
    changes = sorted(snapshot.changes, key=lambda c: c.detected_at, reverse=True)
    return (
        environment(TEMPLATES_DIR)
        .get_template("changes.html")
        .render(
            items=[{"change": c, "dataset": datasets[c.dataset_id]} for c in changes],
            **_shell(snapshot, root="../", active_nav="changes"),
        )
    )


_LINK = re.compile(r'(?:href|src)="([^"]+)"')


def broken_links(output_dir: Path) -> list[str]:
    """Every relative link in the built site that points at nothing.

    External links, in-page anchors and the documentation site (`docs/`, built by
    mkdocs into the same output by deploy.yml) are skipped.
    """
    problems = []
    for page in sorted(output_dir.rglob("*.html")):
        for target in _LINK.findall(page.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path = target.split("#", 1)[0].split("?", 1)[0]
            resolved = (page.parent / path).resolve()
            if resolved == (output_dir / "docs").resolve():
                continue
            if not resolved.exists():
                problems.append(f"{page.relative_to(output_dir)}: {target}")
    return problems


def _write_pages(output_dir: Path, kind: str, pages: dict[str, str]) -> None:
    """Write `<output_dir>/<kind>/<id>/index.html` for each page, replacing old ones."""
    directory = output_dir / kind
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)
    for identifier, html in pages.items():
        page = directory / identifier / "index.html"
        page.parent.mkdir(parents=True)
        page.write_text(html, encoding="utf-8")


def build(output_dir: Path = DEFAULT_OUTPUT, fixtures_dir: Path = FIXTURES_DIR) -> Path:
    """Render the demo site into `output_dir`, including its static assets."""
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "index.html").write_text(render(fixtures_dir), encoding="utf-8")

    snapshot = ProductSnapshot.from_directory(fixtures_dir)
    _write_pages(
        output_dir,
        "datasets",
        {d.id: render_dataset(snapshot, d.id) for d in snapshot.datasets},
    )
    (output_dir / "datasets" / "index.html").write_text(render_catalog(snapshot), encoding="utf-8")
    _write_pages(
        output_dir,
        "incidents",
        {i.id: render_incident(snapshot, i.id) for i in snapshot.incidents},
    )
    _write_pages(
        output_dir, "changes", {c.id: render_change(snapshot, c.id) for c in snapshot.changes}
    )
    (output_dir / "incidents" / "index.html").write_text(
        render_incident_list(snapshot), encoding="utf-8"
    )
    (output_dir / "changes" / "index.html").write_text(
        render_change_list(snapshot), encoding="utf-8"
    )

    static_out = output_dir / "static"
    if static_out.exists():
        shutil.rmtree(static_out)
    shutil.copytree(STATIC_DIR, static_out)

    problems = broken_links(output_dir)
    if problems:
        raise SystemExit("broken internal links:\n" + "\n".join(problems))
    return output_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--fixtures", type=Path, default=FIXTURES_DIR)
    args = parser.parse_args(argv)

    out = build(args.output, args.fixtures)
    print(f"demo site written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
