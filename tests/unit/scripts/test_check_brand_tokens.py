"""The Brand v2 token gate has to actually fail.

#68: Watch uses KPubData Studio Brand v2 unchanged, from one token file. A gate nobody
has watched fail is not a gate, so most of these tests copy the real token file and
document into a temporary repository, plant one kind of drift, and expect exit code 1.
Running against this repository is what makes pytest the CI gate.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = REPO_ROOT / "scripts" / "check_brand_tokens.py"
_TOKEN_FILE = Path("src") / "kpubdata_watch" / "web" / "static" / "brand-v2.css"
_DOC = Path("docs") / "VISUAL_IDENTITY.md"
_PINNED_SHA = "1fbf57e41a32b3ef9cd353666beb1fcd0d6b97e9"


def _run(
    root: Path, *args: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    base = {k: v for k, v in os.environ.items() if k != "STUDIO_GLOBALS_CSS"}
    return subprocess.run(
        [sys.executable, str(_SCRIPT), "--root", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
        env={**base, **(env or {})},
    )


def _repo(tmp_path: Path) -> Path:
    for relative in (_TOKEN_FILE, _DOC):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO_ROOT / relative, target)
    return tmp_path


def _edit(path: Path, old: str, new: str, count: int = 1) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text, old
    path.write_text(text.replace(old, new, count), encoding="utf-8")


def _studio_copy(tmp_path: Path) -> Path:
    """A stand-in for Studio's globals.css: Tailwind preamble plus the same blocks."""
    css = (REPO_ROOT / _TOKEN_FILE).read_text(encoding="utf-8")
    studio = tmp_path / "studio-globals.css"
    studio.write_text('@import "tailwindcss";\n\n' + css + "\n@theme inline {}\n", encoding="utf-8")
    return studio


def test_this_repository_passes() -> None:
    """The case the gate must not break: Watch as it is today."""
    result = _run(REPO_ROOT)
    assert result.returncode == 0, result.stderr
    assert "40 light and 40 dark tokens" in result.stdout


def test_a_clean_copy_passes(tmp_path: Path) -> None:
    result = _run(_repo(tmp_path))
    assert result.returncode == 0, result.stderr


def test_a_changed_token_value_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _edit(root / _TOKEN_FILE, "--status-warning: #b45309;", "--status-warning: #b45308;")

    result = _run(root)

    assert result.returncode == 1
    assert "--status-warning light: table '#b45309', token file '#b45308'" in result.stderr


def test_a_changed_dark_value_in_the_document_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _edit(
        root / _DOC,
        "| `--foreground` | `#172033` | `#e8eaed` |",
        "| `--foreground` | `#172033` | `#ffffff` |",
    )

    result = _run(root)

    assert result.returncode == 1
    assert "--foreground dark" in result.stderr


def test_a_token_missing_from_the_table_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _edit(root / _DOC, "| `--input` | `#d5d9d2` | `#3a3f46` |\n", "")

    result = _run(root)

    assert result.returncode == 1
    assert "--input is in the token file but not in the table" in result.stderr


def test_missing_table_markers_fail(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _edit(root / _DOC, "<!-- brand-v2-tokens:start -->", "")

    result = _run(root)

    assert result.returncode == 1
    assert "token table markers" in result.stderr


def test_repainting_the_brand_in_both_file_and_table_fails(tmp_path: Path) -> None:
    """A matching edit to the file and the table still cannot bring Brand v1 Indigo back."""
    root = _repo(tmp_path)
    _edit(root / _TOKEN_FILE, "--brand-primary: #2563eb;", "--brand-primary: #5b5bd6;", count=-1)
    _edit(
        root / _DOC,
        "| `--brand-primary` | `#2563eb` | `#2563eb` |",
        "| `--brand-primary` | `#5b5bd6` | `#5b5bd6` |",
    )

    result = _run(root)

    assert result.returncode == 1
    assert "light --brand-primary is '#5b5bd6', Brand v2 says '#2563eb'" in result.stderr


def test_a_brand_colour_used_as_status_fails(tmp_path: Path) -> None:
    """Fresh Mint is never success: a status token equal to it is caught."""
    root = _repo(tmp_path)
    _edit(root / _TOKEN_FILE, "--status-success: #15803d;", "--status-success: #14b8a6;")
    _edit(
        root / _DOC,
        "| `--status-success` | `#15803d` |",
        "| `--status-success` | `#14b8a6` |",
    )

    result = _run(root)

    assert result.returncode == 1
    assert "light: --brand-secondary = --status-success (#14b8a6)" in result.stderr


def test_a_var_reference_is_resolved_before_comparing(tmp_path: Path) -> None:
    """`--brand-text: var(--brand-primary)` collides when Brand Blue becomes a status."""
    root = _repo(tmp_path)
    _edit(root / _TOKEN_FILE, "--status-unknown: #52525b;", "--status-unknown: #2563eb;")
    _edit(root / _DOC, "| `--status-unknown` | `#52525b` |", "| `--status-unknown` | `#2563eb` |")

    result = _run(root)

    assert result.returncode == 1
    assert "light: --brand-text = --status-unknown" in result.stderr


def test_os_dark_differing_from_dark_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    css = root / _TOKEN_FILE
    text = css.read_text(encoding="utf-8")
    # The last occurrence is inside the OS-dark media block.
    head, _, tail = text.rpartition("--status-unknown-solid: #71717a;")
    css.write_text(head + "--status-unknown-solid: #71717b;" + tail, encoding="utf-8")

    result = _run(root)

    assert result.returncode == 1
    assert "the OS-dark block differs from the dark block" in result.stderr


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
def test_a_wrong_health_mapping_fails(tmp_path: Path, old: str, new: str, message: str) -> None:
    root = _repo(tmp_path)
    _edit(root / _DOC, old, new)

    result = _run(root)

    assert result.returncode == 1
    assert message in result.stderr


def test_a_studio_link_pinned_elsewhere_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    other = "0" * 40
    (root / "docs" / "UI.md").write_text(
        f"[x](https://github.com/yeongseon/kpubdata-studio/blob/{other}/src/globals.css)\n",
        encoding="utf-8",
    )

    result = _run(root)

    assert result.returncode == 1
    assert f"docs/UI.md:1: links Studio at {other}, tokens are from {_PINNED_SHA}" in result.stderr


def test_a_main_branch_link_is_not_a_pin(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "docs" / "UI.md").write_text(
        "[x](https://github.com/yeongseon/kpubdata-studio/blob/main/README.md)\n",
        encoding="utf-8",
    )
    result = _run(root)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "where",
    [
        Path("ui-lab") / "status-page" / "theme.css",
        Path("ui-lab") / "issues-first" / "index.html",
        Path("src") / "kpubdata_watch" / "web" / "templates" / "base.html.jinja",
    ],
)
def test_a_ui_file_redefining_a_token_fails(tmp_path: Path, where: Path) -> None:
    root = _repo(tmp_path)
    target = root / where
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("<style>:root { --brand-primary: #5b5bd6; }</style>\n", encoding="utf-8")

    result = _run(root)

    assert result.returncode == 1
    assert f"{where.as_posix()}: declares --brand-primary" in result.stderr


def test_a_ui_file_using_the_tokens_passes(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    page = root / "ui-lab" / "status-page" / "index.html"
    page.parent.mkdir(parents=True)
    page.write_text(
        '<link rel="stylesheet" href="../../src/kpubdata_watch/web/static/brand-v2.css">\n'
        "<style>.badge { color: var(--status-success); --badge-gap: 4px; }</style>\n",
        encoding="utf-8",
    )
    result = _run(root)
    assert result.returncode == 0, result.stderr


def test_matching_studio_passes(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    studio = _studio_copy(tmp_path)

    result = _run(root, "--studio", str(studio))

    assert result.returncode == 0, result.stderr
    assert "they match" in result.stdout


def test_studio_drift_fails_through_the_environment_variable(tmp_path: Path) -> None:
    """Studio moved a value; Watch did not follow."""
    root = _repo(tmp_path)
    studio = _studio_copy(tmp_path)
    _edit(studio, "--muted-foreground: #5e6e84;", "--muted-foreground: #64748b;")

    result = _run(root, env={"STUDIO_GLOBALS_CSS": str(studio)})

    assert result.returncode == 1
    assert (
        "drift from Studio: light: --muted-foreground is '#5e6e84' here, '#64748b' in Studio"
        in (result.stderr)
    )


def test_a_token_studio_added_is_drift(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    studio = _studio_copy(tmp_path)
    _edit(studio, "--brand-primary: #2563eb;", "--brand-primary: #2563eb;\n  --brand-new: #000001;")

    result = _run(root, "--studio", str(studio))

    assert result.returncode == 1
    assert "light: --brand-new is None here, '#000001' in Studio" in result.stderr


def test_a_missing_studio_file_fails(tmp_path: Path) -> None:
    result = _run(_repo(tmp_path), "--studio", str(tmp_path / "nope.css"))
    assert result.returncode == 1
    assert "so Studio was not compared" in result.stderr


def test_a_missing_token_file_fails_rather_than_passing_empty(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / _TOKEN_FILE).unlink()
    result = _run(root)
    assert result.returncode == 1
    assert "nothing was checked" in result.stderr
