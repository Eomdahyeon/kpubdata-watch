"""The governance gate has to actually fail.

#3 adopted kpubdata's title and verification rules; POLICY 18.2 says a rule
without a gate is a wish. Most of these tests plant a violation — a template
that stopped asking for a verification level, a title workflow that stopped
failing — in a temporary repository and expect exit code 1.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = REPO_ROOT / "scripts" / "check_governance.py"

# Enough of a template and a titles workflow to satisfy the gate; the gate reads
# them as text, so the surrounding YAML can stay skeletal.
_TEMPLATE_WITH_FIELD = """\
name: 기능 제안
title: "feat: "
body:
  - type: textarea
    id: problem
    attributes:
      label: 해결하려는 문제
    validations:
      required: true
  - type: dropdown
    id: verification
    attributes:
      label: Required Verification (POLICY 18)
      options:
        - V0 — Static (lint, typecheck, schema validation)
    validations:
      required: true
"""

_TEMPLATE_WITHOUT_FIELD = """\
name: 기능 제안
title: "feat: "
body:
  - type: textarea
    id: problem
    attributes:
      label: 해결하려는 문제
    validations:
      required: true
"""

_TITLES_WIRED = """\
name: Titles
on:
  pull_request:
jobs:
  pull-request:
    name: PR title
    steps:
      - name: Parse the title
        id: title
        uses: kpubdata-lab/kpubdata/.github/actions/conventional-title@main
      - name: The title must follow the convention
        run: |
          if [ "${VALID}" != "true" ]; then
            echo "::error::${ERROR}"
            exit 1
          fi
"""


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), "--root", str(root)],
        capture_output=True,
        text=True,
        check=False,
    )


def _repo(
    tmp_path: Path, template: str = _TEMPLATE_WITH_FIELD, titles: str = _TITLES_WIRED
) -> Path:
    directory = tmp_path / ".github" / "ISSUE_TEMPLATE"
    directory.mkdir(parents=True)
    (directory / "feature_request.yml").write_text(template, encoding="utf-8")
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir()
    (workflows / "titles.yml").write_text(titles, encoding="utf-8")
    return tmp_path


def test_this_repository_passes() -> None:
    """The case the gate must not break: Watch as it is today."""
    result = _run(REPO_ROOT)
    assert result.returncode == 0, result.stderr


def test_a_minimal_repository_passes(tmp_path: Path) -> None:
    result = _run(_repo(tmp_path))
    assert result.returncode == 0, result.stderr


def test_a_template_without_the_verification_field_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path, template=_TEMPLATE_WITHOUT_FIELD)

    result = _run(root)

    assert result.returncode == 1
    assert "feature_request.yml" in result.stderr
    assert "verification" in result.stderr


def test_only_one_template_losing_the_field_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / ".github" / "ISSUE_TEMPLATE" / "docs.yml").write_text(
        _TEMPLATE_WITHOUT_FIELD, encoding="utf-8"
    )

    result = _run(root)

    assert result.returncode == 1
    assert "docs.yml" in result.stderr
    assert "feature_request.yml" not in result.stderr


def test_config_yml_is_exempt(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / ".github" / "ISSUE_TEMPLATE" / "config.yml").write_text(
        "blank_issues_enabled: false\n", encoding="utf-8"
    )

    result = _run(root)

    assert result.returncode == 0, result.stderr


def test_an_empty_template_directory_fails_rather_than_passing(tmp_path: Path) -> None:
    directory = tmp_path / ".github" / "ISSUE_TEMPLATE"
    directory.mkdir(parents=True)
    # Only the exempt config.yml: the directory holds no template to check.
    (directory / "config.yml").write_text("blank_issues_enabled: false\n", encoding="utf-8")
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir()
    (workflows / "titles.yml").write_text(_TITLES_WIRED, encoding="utf-8")

    result = _run(tmp_path)

    assert result.returncode == 1
    assert "no issue template" in result.stderr


def test_a_missing_template_directory_fails(tmp_path: Path) -> None:
    root = tmp_path / ".github" / "workflows"
    root.mkdir(parents=True)
    (root / "titles.yml").write_text(_TITLES_WIRED, encoding="utf-8")

    result = _run(tmp_path)

    assert result.returncode == 1
    assert "ISSUE_TEMPLATE" in result.stderr


def test_removing_the_shared_title_action_fails(tmp_path: Path) -> None:
    titles = _TITLES_WIRED.replace(
        "kpubdata-lab/kpubdata/.github/actions/conventional-title", "actions/checkout@v7"
    )
    result = _run(_repo(tmp_path, titles=titles))

    assert result.returncode == 1
    assert "conventional-title action is gone" in result.stderr


def test_removing_the_failing_step_fails(tmp_path: Path) -> None:
    result = _run(_repo(tmp_path, titles=_TITLES_WIRED.replace("exit 1", "exit 0")))

    assert result.returncode == 1
    assert "no longer fails" in result.stderr


def test_a_missing_titles_workflow_fails(tmp_path: Path) -> None:
    directory = tmp_path / ".github" / "ISSUE_TEMPLATE"
    directory.mkdir(parents=True)
    (directory / "feature_request.yml").write_text(_TEMPLATE_WITH_FIELD, encoding="utf-8")

    result = _run(tmp_path)

    assert result.returncode == 1
    assert "titles.yml" in result.stderr
