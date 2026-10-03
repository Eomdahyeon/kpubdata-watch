#!/usr/bin/env python3
"""Render the Public Status page with fixture data into a static demo site (#78).

GitHub Pages hosts a fixture-based demo of the Public Status page, not the live
service (see docs/decisions — the production service stays FastAPI + worker +
PostgreSQL and never runs on Pages). This script renders
`src/kpubdata_watch/web/templates/public_status.html` with the product snapshot in
`demo/fixtures/` (five files, loaded through the public read models, #82) into a
self-contained output directory that `.github/workflows/deploy.yml` uploads to Pages.
Times are shown as clock times in KST, never as "3m ago": a static page is read long
after it is built.

Usage:
    python scripts/build_demo.py [--output _site] [--fixtures demo/fixtures]
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Any

from kpubdata_watch.api.read_models.public import CHECK_NAMES
from kpubdata_watch.api.read_models.snapshot import ProductSnapshot
from kpubdata_watch.web.presentation import (
    CHANGE_ICON,
    HEALTH_META,
    HEALTH_ORDER,
    STATIC_DIR,
    TEMPLATES_DIR,
    environment,
    kst_datetime,
    kst_minute,
    kst_time,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = REPO_ROOT / "demo" / "fixtures"
DEFAULT_OUTPUT = REPO_ROOT / "_site"
# The product pages this demo builds; the navigation links only to these (#83).
BUILT_PAGES = frozenset({"overview"})

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


def render(fixtures_dir: Path = FIXTURES_DIR) -> str:
    """Render the Public Status page to a single HTML string."""
    template = environment(TEMPLATES_DIR).get_template("public_status.html")
    snapshot = ProductSnapshot.from_directory(fixtures_dir)
    datasets = dataset_rows(snapshot)
    return template.render(
        datasets=datasets,
        counts=health_counts(datasets),
        total=len(datasets),
        root="",
        active_nav="overview",
        built_pages=BUILT_PAGES,
        snapshot_at=kst_minute(snapshot.generated_at),
    )


def build(output_dir: Path = DEFAULT_OUTPUT, fixtures_dir: Path = FIXTURES_DIR) -> Path:
    """Render the demo site into `output_dir`, including its static assets."""
    output_dir.mkdir(parents=True, exist_ok=True)
    html = render(fixtures_dir)
    (output_dir / "index.html").write_text(html, encoding="utf-8")

    static_out = output_dir / "static"
    if static_out.exists():
        shutil.rmtree(static_out)
    shutil.copytree(STATIC_DIR, static_out)

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
