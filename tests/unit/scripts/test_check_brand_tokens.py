"""`scripts/check_brand_tokens.py` fails on every kind of Brand v2 drift (#72).

The script is driven through ``subprocess`` like the other gates here. Each
negative case starts from Watch's real token file used as its own "Studio",
which passes, and changes exactly one thing.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "check_brand_tokens.py"
WATCH_TOKENS = REPO_ROOT / "src" / "kpubdata_watch" / "web" / "static" / "brand-v2.css"

LIGHT_SUCCESS = "--status-success: #15803d;"


def _run(studio: Path, watch: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--studio", str(studio), "--watch", str(watch)],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def studio(tmp_path: Path) -> Path:
    path = tmp_path / "globals.css"
    path.write_text(WATCH_TOKENS.read_text(encoding="utf-8"), encoding="utf-8")
    return path


def _watch(tmp_path: Path, old: str, new: str) -> Path:
    css = WATCH_TOKENS.read_text(encoding="utf-8")
    assert old in css, f"{old!r} is not in brand-v2.css; update the test"
    path = tmp_path / "brand-v2.css"
    path.write_text(css.replace(old, new, 1), encoding="utf-8")
    return path


def test_identical_tokens_pass(studio: Path) -> None:
    result = _run(studio, WATCH_TOKENS)
    assert result.returncode == 0, result.stderr


def test_a_changed_value_fails(studio: Path, tmp_path: Path) -> None:
    watch = _watch(tmp_path, "--brand-primary: #2563eb;", "--brand-primary: #2563ec;")
    result = _run(studio, watch)
    assert result.returncode == 1
    assert "--brand-primary is #2563ec, Studio has #2563eb" in result.stderr


def test_a_missing_token_fails(studio: Path, tmp_path: Path) -> None:
    result = _run(studio, _watch(tmp_path, LIGHT_SUCCESS, ""))
    assert result.returncode == 1
    assert "missing --status-success" in result.stderr


def test_fresh_mint_as_healthy_fails(studio: Path, tmp_path: Path) -> None:
    css = WATCH_TOKENS.read_text(encoding="utf-8")
    mint = css.split("--brand-secondary:", 1)[1].split(";", 1)[0].strip()
    result = _run(studio, _watch(tmp_path, LIGHT_SUCCESS, f"--status-success: {mint};"))
    assert result.returncode == 1
    assert "--status-success uses Fresh Mint" in result.stderr


def test_brand_blue_in_a_status_token_fails(studio: Path, tmp_path: Path) -> None:
    result = _run(studio, _watch(tmp_path, LIGHT_SUCCESS, "--status-success: #2563eb;"))
    assert result.returncode == 1
    assert "--status-success uses Brand Blue" in result.stderr


def test_a_studio_file_without_the_theme_blocks_fails(tmp_path: Path) -> None:
    empty = tmp_path / "globals.css"
    empty.write_text("@theme { --font-sans: system-ui; }\n", encoding="utf-8")
    result = _run(empty, WATCH_TOKENS)
    assert result.returncode == 1
    assert "the comparison cannot run" in result.stderr
