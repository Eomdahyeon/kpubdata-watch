"""`scripts/check_brand_tokens.py` fails on every kind of Brand v2 drift (#68, #72).

#68: Watch uses KPubData Studio Brand v2 unchanged, from one token file. A gate nobody
has watched fail is not a gate, so most of these tests copy the real token file and
document into a temporary repository, plant one kind of drift, and expect exit code 1.
Running against this repository is what makes pytest the CI gate.

`--studio` is required (unless `--contrast`, #91): most tests pass an unedited copy of
Watch's own token file as a stand-in for Studio, which reports no drift by itself, so the
failure each test observes comes from the one change it made.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "check_brand_tokens.py"
TOKEN_FILE = Path("src") / "kpubdata_watch" / "web" / "static" / "brand-v2.css"
DOC = Path("docs") / "VISUAL_IDENTITY.md"
PINNED_SHA = "1fbf57e41a32b3ef9cd353666beb1fcd0d6b97e9"


def _run(root: Path, studio: Path | None, *args: str) -> subprocess.CompletedProcess[str]:
    """Run the script against `root`, with `studio` as `--studio` unless it is None."""
    base = {k: v for k, v in os.environ.items() if k != "STUDIO_GLOBALS_CSS"}
    extra = ["--studio", str(studio)] if studio is not None else []
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *extra, *args],
        capture_output=True,
        text=True,
        check=False,
        env=base,
    )


def _repo(tmp_path: Path) -> Path:
    for relative in (TOKEN_FILE, DOC):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO_ROOT / relative, target)
    return tmp_path


def _edit(path: Path, old: str, new: str, count: int = 1) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text, old
    path.write_text(text.replace(old, new, count), encoding="utf-8")


def _studio_copy(tmp_path: Path, name: str = "studio-globals.css") -> Path:
    """A stand-in for Studio's globals.css: Tailwind preamble plus the same blocks."""
    css = (REPO_ROOT / TOKEN_FILE).read_text(encoding="utf-8")
    studio = tmp_path / name
    studio.write_text('@import "tailwindcss";\n\n' + css + "\n@theme inline {}\n", encoding="utf-8")
    return studio


@pytest.fixture
def studio(tmp_path: Path) -> Path:
    """An unedited stand-in for Studio: by itself, reports no drift."""
    return _studio_copy(tmp_path)


def test_this_repository_passes(studio: Path) -> None:
    """The case the gate must not break: Watch as it is today."""
    result = _run(REPO_ROOT, studio)
    assert result.returncode == 0, result.stderr
    assert "40 light and 40 dark tokens" in result.stdout
    assert "24 pairs at or above 4.5:1" in result.stdout
    assert (
        "lowest light Degraded #b45309 on --status-warning-subtle #fef3c7 = 4.51:1" in result.stdout
    )


def test_a_clean_copy_passes(tmp_path: Path, studio: Path) -> None:
    result = _run(_repo(tmp_path), studio)
    assert result.returncode == 0, result.stderr


def test_studio_is_required_unless_contrast(tmp_path: Path) -> None:
    result = _run(_repo(tmp_path), None)
    assert result.returncode == 2
    assert "--studio is required" in result.stderr


def test_contrast_works_without_studio(tmp_path: Path) -> None:
    result = _run(_repo(tmp_path), None, "--contrast")
    assert result.returncode == 0, result.stderr
    assert "| light | Healthy |" in result.stdout


# --- docs/VISUAL_IDENTITY.md table sync ------------------------------------------------


def test_a_changed_token_value_fails(tmp_path: Path, studio: Path) -> None:
    root = _repo(tmp_path)
    _edit(root / TOKEN_FILE, "--status-warning: #b45309;", "--status-warning: #b45308;")

    result = _run(root, studio)

    assert result.returncode == 1
    assert "--status-warning light: table '#b45309', token file '#b45308'" in result.stderr


def test_a_changed_dark_value_in_the_document_fails(tmp_path: Path, studio: Path) -> None:
    root = _repo(tmp_path)
    _edit(
        root / DOC,
        "| `--foreground` | `#172033` | `#e8eaed` |",
        "| `--foreground` | `#172033` | `#ffffff` |",
    )

    result = _run(root, studio)

    assert result.returncode == 1
    assert "--foreground dark" in result.stderr


def test_a_token_missing_from_the_table_fails(tmp_path: Path, studio: Path) -> None:
    root = _repo(tmp_path)
    _edit(root / DOC, "| `--input` | `#d5d9d2` | `#3a3f46` |\n", "")

    result = _run(root, studio)

    assert result.returncode == 1
    assert "--input is in the token file but not in the table" in result.stderr


def test_missing_table_markers_fail(tmp_path: Path, studio: Path) -> None:
    root = _repo(tmp_path)
    _edit(root / DOC, "<!-- brand-v2-tokens:start -->", "")

    result = _run(root, studio)

    assert result.returncode == 1
    assert "token table markers" in result.stderr


# --- brand/status separation and Studio drift ------------------------------------------


def test_repainting_the_brand_in_both_file_and_table_is_caught_as_drift(
    tmp_path: Path, studio: Path
) -> None:
    """A matching edit to the file and the table still cannot bring Brand v1 Indigo back:

    Studio is canonical, so a repaint that agrees with itself still disagrees with Studio.
    """
    root = _repo(tmp_path)
    _edit(root / TOKEN_FILE, "--brand-primary: #2563eb;", "--brand-primary: #5b5bd6;", count=-1)
    _edit(
        root / DOC,
        "| `--brand-primary` | `#2563eb` | `#2563eb` |",
        "| `--brand-primary` | `#5b5bd6` | `#5b5bd6` |",
    )

    result = _run(root, studio)

    assert result.returncode == 1
    assert (
        "drift from Studio: light: --brand-primary is '#5b5bd6' here, '#2563eb' in Studio"
        in result.stderr
    )


def test_a_brand_colour_used_as_status_fails(tmp_path: Path, studio: Path) -> None:
    """Fresh Mint is never success: a status token equal to it is caught."""
    root = _repo(tmp_path)
    _edit(root / TOKEN_FILE, "--status-success: #15803d;", "--status-success: #14b8a6;")
    _edit(
        root / DOC,
        "| `--status-success` | `#15803d` |",
        "| `--status-success` | `#14b8a6` |",
    )

    result = _run(root, studio)

    assert result.returncode == 1
    assert "brand colour used as status: light: --brand-secondary = --status-success" in (
        result.stderr
    )


def test_a_var_reference_is_resolved_before_comparing(tmp_path: Path, studio: Path) -> None:
    """`--brand-text: var(--brand-primary)` collides when Brand Blue becomes a status."""
    root = _repo(tmp_path)
    _edit(root / TOKEN_FILE, "--status-unknown: #52525b;", "--status-unknown: #2563eb;")
    _edit(root / DOC, "| `--status-unknown` | `#52525b` |", "| `--status-unknown` | `#2563eb` |")

    result = _run(root, studio)

    assert result.returncode == 1
    assert "brand colour used as status: light: --brand-text = --status-unknown" in result.stderr


def test_os_dark_differing_from_dark_fails(tmp_path: Path, studio: Path) -> None:
    root = _repo(tmp_path)
    css = root / TOKEN_FILE
    text = css.read_text(encoding="utf-8")
    # The last occurrence is inside the OS-dark media block.
    head, _, tail = text.rpartition("--status-unknown-solid: #71717a;")
    css.write_text(head + "--status-unknown-solid: #71717b;" + tail, encoding="utf-8")

    result = _run(root, studio)

    assert result.returncode == 1
    assert "the OS-dark block differs from the dark block" in result.stderr


def test_matching_studio_passes(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    studio_file = _studio_copy(tmp_path)

    result = _run(root, studio_file)

    assert result.returncode == 0, result.stderr
    assert "they match" in result.stdout


def test_studio_drift_fails_through_the_studio_flag(tmp_path: Path) -> None:
    """Studio moved a value; Watch did not follow."""
    root = _repo(tmp_path)
    studio_file = _studio_copy(tmp_path)
    _edit(studio_file, "--muted-foreground: #5e6e84;", "--muted-foreground: #64748b;")

    result = _run(root, studio_file)

    assert result.returncode == 1
    assert (
        "drift from Studio: light: --muted-foreground is '#5e6e84' here, '#64748b' in Studio"
        in result.stderr
    )


def test_a_token_studio_added_is_drift(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    studio_file = _studio_copy(tmp_path)
    _edit(
        studio_file,
        "--brand-primary: #2563eb;",
        "--brand-primary: #2563eb;\n  --brand-new: #000001;",
    )

    result = _run(root, studio_file)

    assert result.returncode == 1
    assert "light: --brand-new is None here, '#000001' in Studio" in result.stderr


def test_a_missing_studio_file_fails(tmp_path: Path, studio: Path) -> None:
    result = _run(_repo(tmp_path), tmp_path / "nope.css")
    assert result.returncode == 1
    assert "so Studio was not compared" in result.stderr


def test_a_studio_file_without_the_theme_blocks_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    empty = tmp_path / "empty-globals.css"
    empty.write_text("@theme { --font-sans: system-ui; }\n", encoding="utf-8")

    result = _run(root, empty)

    assert result.returncode == 1
    assert "drift from Studio: light: Studio's stylesheet has no such block" in result.stderr


def test_a_missing_token_file_fails_rather_than_passing_empty(tmp_path: Path, studio: Path) -> None:
    root = _repo(tmp_path)
    (root / TOKEN_FILE).unlink()
    result = _run(root, studio)
    assert result.returncode == 1
    assert "nothing was checked" in result.stderr


# --- Health table -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        (
            "| Healthy | `--status-success` |",
            "| Healthy | `--brand-secondary` |",
            "Health Healthy maps to --brand-secondary, which is not a --status-* token",
        ),
        (
            "| Unknown | `--status-unknown` | ? | `Unknown` |\n",
            "",
            "Health Unknown has no token",
        ),
        (
            "| Critical | `--status-failure` |",
            "| Critical | `--status-critical` |",
            "--status-critical, which the token file does not define",
        ),
    ],
)
def test_a_wrong_health_mapping_fails(
    tmp_path: Path, studio: Path, old: str, new: str, message: str
) -> None:
    root = _repo(tmp_path)
    _edit(root / DOC, old, new)

    result = _run(root, studio)

    assert result.returncode == 1
    assert message in result.stderr


# --- pinned Studio SHA links ---------------------------------------------------------


def test_a_studio_link_pinned_elsewhere_fails(tmp_path: Path, studio: Path) -> None:
    root = _repo(tmp_path)
    other = "0" * 40
    (root / "docs" / "UI.md").write_text(
        f"[x](https://github.com/kpubdata-lab/kpubdata-studio/blob/{other}/src/globals.css)\n",
        encoding="utf-8",
    )

    result = _run(root, studio)

    assert result.returncode == 1
    assert f"docs/UI.md:1: links Studio at {other}, tokens are from {PINNED_SHA}" in result.stderr


def test_a_main_branch_link_is_not_a_pin(tmp_path: Path, studio: Path) -> None:
    root = _repo(tmp_path)
    (root / "docs" / "UI.md").write_text(
        "[x](https://github.com/kpubdata-lab/kpubdata-studio/blob/main/README.md)\n",
        encoding="utf-8",
    )
    result = _run(root, studio)
    assert result.returncode == 0, result.stderr


# --- UI-Lab / web/ redefinition -------------------------------------------------------


@pytest.mark.parametrize(
    "where",
    [
        Path("ui-lab") / "status-page" / "theme.css",
        Path("ui-lab") / "issues-first" / "index.html",
        Path("src") / "kpubdata_watch" / "web" / "templates" / "base.html.jinja",
    ],
)
def test_a_ui_file_redefining_a_token_fails(tmp_path: Path, studio: Path, where: Path) -> None:
    root = _repo(tmp_path)
    target = root / where
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("<style>:root { --brand-primary: #5b5bd6; }</style>\n", encoding="utf-8")

    result = _run(root, studio)

    assert result.returncode == 1
    assert f"{where.as_posix()}: declares --brand-primary" in result.stderr


def test_a_ui_file_using_the_tokens_passes(tmp_path: Path, studio: Path) -> None:
    root = _repo(tmp_path)
    page = root / "ui-lab" / "status-page" / "index.html"
    page.parent.mkdir(parents=True)
    page.write_text(
        '<link rel="stylesheet" href="../../src/kpubdata_watch/web/static/brand-v2.css">\n'
        "<style>.badge { color: var(--status-success); --badge-gap: 4px; }</style>\n",
        encoding="utf-8",
    )
    result = _run(root, studio)
    assert result.returncode == 0, result.stderr


# --- WCAG contrast ---------------------------------------------------------------------


def _module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_brand_tokens", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("first", "second", "expected"),
    [
        ("#000000", "#ffffff", 21.0),
        ("#ffffff", "#ffffff", 1.0),
        ("#b45309", "#fef3c7", 4.51),  # Degraded on its badge, light: the lowest pair
        ("#fef3c7", "#b45309", 4.51),  # order does not matter
        ("#15803d", "#dcfce7", 4.57),
    ],
)
def test_contrast_ratio_follows_wcag_2_1(first: str, second: str, expected: float) -> None:
    assert round(_module().contrast_ratio(first, second), 2) == expected


def test_contrast_prints_the_24_health_pairs(tmp_path: Path) -> None:
    result = _run(_repo(tmp_path), None, "--contrast")
    assert result.returncode == 0, result.stderr
    rows = [
        line
        for line in result.stdout.splitlines()
        if line.startswith("| light") or line.startswith("| dark")
    ]
    assert len(rows) == 24
    assert (
        "| light | Degraded | `--status-warning` `#b45309` | `--status-warning-subtle` `#fef3c7` | 4.51:1 |"
        in rows
    )


def test_lowering_a_status_contrast_below_4_5_fails(tmp_path: Path, studio: Path) -> None:
    """#b6540a is a shade lighter than Degraded's #b45309: 4.43:1 on its badge background."""
    root = _repo(tmp_path)
    _edit(root / TOKEN_FILE, "--status-warning: #b45309;", "--status-warning: #b6540a;")
    _edit(root / DOC, "| `--status-warning` | `#b45309` |", "| `--status-warning` | `#b6540a` |")

    result = _run(root, studio)

    assert result.returncode == 1
    assert (
        "light Degraded: --status-warning #b6540a on --status-warning-subtle #fef3c7 is 4.4"
        in result.stderr
    )
    assert "below 4.5:1" in result.stderr


def test_a_contrast_table_not_pasted_from_the_script_fails(tmp_path: Path, studio: Path) -> None:
    root = _repo(tmp_path)
    _edit(root / DOC, "| 4.51:1 |", "| 4.60:1 |")

    result = _run(root, studio)

    assert result.returncode == 1
    assert "the contrast table is not what `--contrast` prints" in result.stderr


def test_missing_contrast_markers_fail(tmp_path: Path, studio: Path) -> None:
    root = _repo(tmp_path)
    _edit(root / DOC, "<!-- health-contrast:start -->", "")

    result = _run(root, studio)

    assert result.returncode == 1
    assert "contrast table markers" in result.stderr
