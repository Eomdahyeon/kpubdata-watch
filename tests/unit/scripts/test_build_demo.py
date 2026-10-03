"""`scripts/build_demo.py` renders the Public Status demo without error (#78).

GitHub Pages hosts a fixture-based demo, never the live service, so the only
thing this script must prove is that the template renders every health state
with its icon and text, the demo banner is always visible, colour comes only
from brand-v2.css tokens, and the assets the page links actually exist in the
output directory it writes.

`scripts/` is not an importable package (every other script here is a
standalone CLI, run with ``python scripts/<name>.py`` -- see
``test_check_independence.py`` and ``test_check_governance.py``, which drive
their scripts through ``subprocess``). ``build_demo.py`` is loaded the same
CLI way for the end-to-end checks, and through ``importlib`` for the
finer-grained content assertions below, rather than mutating ``sys.path``.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "build_demo.py"
TEMPLATE_FILES = [
    REPO_ROOT / "src" / "kpubdata_watch" / "web" / "templates" / "base.html",
    REPO_ROOT / "src" / "kpubdata_watch" / "web" / "templates" / "public_status.html",
]
DEMO_CSS = REPO_ROOT / "src" / "kpubdata_watch" / "web" / "static" / "demo.css"

# A bare hex colour such as #2563eb or #fff. Comments are stripped before this
# runs, so a match here is a colour written outside brand-v2.css.
HEX_COLOR = re.compile(r"#[0-9a-fA-F]{3,8}\b")
CSS_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
LINK_ATTR = re.compile(r'(?:href|src)="([^"]+)"')


def _load_build_demo() -> ModuleType:
    spec = importlib.util.spec_from_file_location("build_demo", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def build_demo() -> ModuleType:
    return _load_build_demo()


def _all_health_fixtures(tmp_path: Path) -> Path:
    """A minimal five-file snapshot covering every health state, including a
    Change-only Healthy row, independent of the real demo data."""
    now = "2026-10-02T21:15:00+09:00"
    ok = {"status": "pass", "summary": None}

    def dataset(key: str, health: str, **extra: Any) -> dict[str, Any]:
        checks = {name: dict(ok) for name in ("availability", "freshness", "contract", "quality")}
        checks.update(extra.pop("checks", {}))
        return {
            "id": f"fixture-{key}",
            "name": f"{key.capitalize()} Dataset",
            "provider": {"id": "example", "name": "Example Provider"},
            "category": "example",
            "health": health,
            "checks": checks,
            "last_checked_at": now,
            **extra,
        }

    def incident(key: str, check: str, severity: str, title: str) -> dict[str, Any]:
        return {
            "id": f"inc-{key}",
            "dataset_id": f"fixture-{key}",
            "check": check,
            "severity": severity,
            "status": "ongoing",
            "title": title,
            "summary": title,
            "started_at": now,
            "detected_at": now,
            "evidence": {
                "expected": {"x": 1},
                "observed": {"x": 2},
                "difference": {"x": 1},
                "rule": {"id": "example.rule", "description": "Example rule"},
                "first_seen_at": now,
            },
            "timeline": [],
        }

    datasets = [
        dataset("healthy", "healthy"),
        dataset("changed", "healthy", latest_change_ids=["chg-changed"]),
        dataset("degraded", "degraded", active_incident_ids=["inc-degraded"]),
        dataset("critical", "critical", active_incident_ids=["inc-critical"]),
        dataset(
            "unknown",
            "unknown",
            checks={"availability": {"status": "unknown", "summary": "Probe failed (D-009)"}},
        ),
    ]
    files: dict[str, Any] = {
        "snapshot": {"generated_at": now},
        "datasets": datasets,
        "incidents": [
            incident("degraded", "freshness", "warning", "Freshness delayed"),
            incident("critical", "contract", "critical", "Breaking contract change"),
        ],
        "changes": [
            {
                "id": "chg-changed",
                "dataset_id": "fixture-changed",
                "change_type": "contract",
                "severity": "info",
                "title": "Contract changed",
                "summary": "A field was added.",
                "detected_at": now,
                "diff": {"added": ["x:string"]},
                "health_impact": "none",
            }
        ],
        "histories": [
            {
                "dataset_id": row["id"],
                "days": [
                    {
                        "date": (date(2026, 10, 2) - timedelta(days=n)).isoformat(),
                        "health": "healthy",
                    }
                    for n in range(29, -1, -1)
                ],
            }
            for row in datasets
        ],
    }
    directory = tmp_path / "fixtures"
    directory.mkdir()
    for name, content in files.items():
        (directory / f"{name}.json").write_text(json.dumps(content), encoding="utf-8")
    return directory


def test_cli_renders_without_error(tmp_path: Path) -> None:
    out = tmp_path / "_site"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--output", str(out)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    index = out / "index.html"
    assert index.is_file()
    assert index.read_text(encoding="utf-8").strip()


def test_build_copies_static_assets(build_demo: ModuleType, tmp_path: Path) -> None:
    out = build_demo.build(output_dir=tmp_path / "_site")
    static_dir = out / "static"
    for name in ("brand-v2.css", "demo.css", "favicon.svg", "kpubdata-symbol.svg"):
        assert (static_dir / name).is_file(), f"{name} missing from built static/"


def test_demo_banner_is_present_in_both_languages(build_demo: ModuleType) -> None:
    html = build_demo.render()
    assert "데모" in html
    assert "fixed sample data" in html


def test_every_health_state_renders_with_icon_and_text(
    build_demo: ModuleType, tmp_path: Path
) -> None:
    fixtures = _all_health_fixtures(tmp_path)
    html = build_demo.render(fixtures)
    for key, meta in build_demo.HEALTH_META.items():
        assert meta["icon"] in html, f"missing icon for {key}"
        assert meta["label"] in html, f"missing label for {key}"
    # The Change-only Healthy row renders the neutral info glyph, not a colour.
    assert build_demo.CHANGE_ICON in html
    assert "Contract changed" in html


def test_health_counts_match_the_fixtures(build_demo: ModuleType, tmp_path: Path) -> None:
    fixtures = _all_health_fixtures(tmp_path)
    datasets = build_demo.load_datasets(fixtures)
    counts = build_demo.health_counts(datasets)
    assert counts == {"healthy": 2, "degraded": 1, "critical": 1, "unknown": 1}


@pytest.mark.parametrize("path", TEMPLATE_FILES + [DEMO_CSS])
def test_no_raw_hex_color_outside_brand_v2_css(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = CSS_COMMENT.sub("", text)
    assert not HEX_COLOR.search(text), f"{path} has a raw hex colour; use var(--...) instead"


def test_output_links_resolve(build_demo: ModuleType, tmp_path: Path) -> None:
    out = build_demo.build(output_dir=tmp_path / "_site")
    html = (out / "index.html").read_text(encoding="utf-8")
    for target in LINK_ATTR.findall(html):
        if target.startswith(("http://", "https://", "docs/", "#")):
            # External links, in-page anchors, and the mkdocs site deploy.yml
            # builds alongside this output, do not exist until the full
            # workflow runs.
            continue
        assert (out / target).exists(), f"linked asset {target!r} does not resolve"
