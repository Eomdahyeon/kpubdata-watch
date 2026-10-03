#!/usr/bin/env python3
"""Render the Public Status page with fixture data into a static demo site (#78).

GitHub Pages hosts a fixture-based demo of the Public Status page, not the live
service (see docs/decisions — the production service stays FastAPI + worker +
PostgreSQL and never runs on Pages). This script renders
`src/kpubdata_watch/web/templates/public_status.html` with
`demo/fixtures/datasets.json` into a self-contained output directory that
`.github/workflows/deploy.yml` uploads to Pages.

Usage:
    python scripts/build_demo.py [--output _site] [--fixtures demo/fixtures/datasets.json]
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from kpubdata_watch.web.presentation import (
    CHANGE_ICON,
    HEALTH_META,
    HEALTH_ORDER,
    STATIC_DIR,
    TEMPLATES_DIR,
    environment,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_PATH = REPO_ROOT / "demo" / "fixtures" / "datasets.json"
DEFAULT_OUTPUT = REPO_ROOT / "_site"

# The health vocabulary and the Jinja environment come from the package
# (kpubdata_watch.web.presentation, #73); HEALTH_META, HEALTH_ORDER and
# CHANGE_ICON are re-exported here for the tests and for readers of this script.
__all__ = ["CHANGE_ICON", "HEALTH_META", "HEALTH_ORDER", "build", "render"]


def load_datasets(path: Path = FIXTURES_PATH) -> list[dict[str, Any]]:
    """Load the fixture datasets, rejecting a health state the page cannot show.

    The icons and labels come from the template primitives, so a row needs no
    display fields of its own.
    """
    rows: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))
    for row in rows:
        if row["health"] not in HEALTH_META:
            raise ValueError(f"{row['dataset_id']}: unknown health {row['health']!r}")
    return rows


def health_counts(datasets: list[dict[str, Any]]) -> dict[str, int]:
    """Count datasets per health state, in `HEALTH_ORDER`."""
    counts = dict.fromkeys(HEALTH_ORDER, 0)
    for row in datasets:
        counts[row["health"]] += 1
    return counts


def render(fixtures_path: Path = FIXTURES_PATH) -> str:
    """Render the Public Status page to a single HTML string."""
    template = environment(TEMPLATES_DIR).get_template("public_status.html")
    datasets = load_datasets(fixtures_path)
    return template.render(
        datasets=datasets,
        counts=health_counts(datasets),
        total=len(datasets),
    )


def build(output_dir: Path = DEFAULT_OUTPUT, fixtures_path: Path = FIXTURES_PATH) -> Path:
    """Render the demo site into `output_dir`, including its static assets."""
    output_dir.mkdir(parents=True, exist_ok=True)
    html = render(fixtures_path)
    (output_dir / "index.html").write_text(html, encoding="utf-8")

    static_out = output_dir / "static"
    if static_out.exists():
        shutil.rmtree(static_out)
    shutil.copytree(STATIC_DIR, static_out)

    return output_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--fixtures", type=Path, default=FIXTURES_PATH)
    args = parser.parse_args(argv)

    out = build(args.output, args.fixtures)
    print(f"demo site written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
