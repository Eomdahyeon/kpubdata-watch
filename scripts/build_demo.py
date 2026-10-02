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

from jinja2 import Environment, FileSystemLoader, select_autoescape

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = REPO_ROOT / "src" / "kpubdata_watch" / "web" / "templates"
STATIC_DIR = REPO_ROOT / "src" / "kpubdata_watch" / "web" / "static"
FIXTURES_PATH = REPO_ROOT / "demo" / "fixtures" / "datasets.json"
DEFAULT_OUTPUT = REPO_ROOT / "_site"

# Health -> (label, icon). Matches docs/UI.md PRD §53's visual cues: text and an
# icon always travel with the colour, never colour alone.
HEALTH_META: dict[str, dict[str, str]] = {
    "healthy": {"label": "Healthy", "icon": "●"},  # ●
    "degraded": {"label": "Degraded", "icon": "▲"},  # ▲
    "critical": {"label": "Critical", "icon": "✕"},  # ✕
    "unknown": {"label": "Unknown", "icon": "?"},
}
# An active issue reuses its row's health icon; a Change is always the neutral
# "info" glyph, never a health colour (PRD §46, §53).
CHANGE_ICON = "ⓘ"  # ⓘ
HEALTH_ORDER = ("healthy", "degraded", "critical", "unknown")


def load_datasets(path: Path = FIXTURES_PATH) -> list[dict[str, Any]]:
    """Load fixture datasets and attach the display metadata the template reads."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    enriched: list[dict[str, Any]] = []
    for row in raw:
        health = row["health"]
        if health not in HEALTH_META:
            raise ValueError(f"{row['dataset_id']}: unknown health {health!r}")
        meta = HEALTH_META[health]
        enriched.append(
            {
                **row,
                "status_label": meta["label"],
                "status_icon": meta["icon"],
                "issue_icon": meta["icon"] if row.get("issue") else None,
                "change_icon": CHANGE_ICON if row.get("change") else None,
            }
        )
    return enriched


def health_counts(datasets: list[dict[str, Any]]) -> dict[str, int]:
    """Count datasets per health state, in `HEALTH_ORDER`."""
    counts = dict.fromkeys(HEALTH_ORDER, 0)
    for row in datasets:
        counts[row["health"]] += 1
    return counts


def render(fixtures_path: Path = FIXTURES_PATH) -> str:
    """Render the Public Status page to a single HTML string."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("public_status.html")
    datasets = load_datasets(fixtures_path)
    return template.render(
        datasets=datasets,
        counts=health_counts(datasets),
        total=len(datasets),
        health_order=HEALTH_ORDER,
        health_meta=HEALTH_META,
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
