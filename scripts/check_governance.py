#!/usr/bin/env python3
"""The governance rules adopted from kpubdata stay wired (#3).

Two rules out of kpubdata POLICY are enforced here, because a rule without a
gate is a wish (POLICY 18.2):

- every issue template asks for a Required Verification level (POLICY 18), so
  triage never meets an issue that forgot to choose one: a template without a
  `verification` field fails;
- the pull-request title gate stays wired (POLICY 2.1.3): `.github/workflows/
  titles.yml` must keep calling the series' shared conventional-title action
  and must keep a step that exits non-zero on an invalid title. Removing the
  gate must not pass CI silently.

The files are scanned as text rather than parsed: PyYAML is not a dependency,
and one simple scan is easier to trust than a hand-rolled parser.

Usage:
    python scripts/check_governance.py [--root PATH]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

TEMPLATES_DIR = Path(".github") / "ISSUE_TEMPLATE"
TITLES_WORKFLOW = Path(".github") / "workflows" / "titles.yml"
TEMPLATE_EXEMPT = ("config.yml",)

# `config.yml` chooses templates; it is not one, so it carries no field.
SHARED_TITLE_ACTION = "yeongseon/kpubdata/.github/actions/conventional-title"
_FAILING_STEP = "exit 1"

_VERIFICATION_FIELD = re.compile(r"^\s*id:\s*verification\s*$", re.MULTILINE)


def template_violations(root: Path) -> tuple[list[str], int]:
    """Templates that stopped asking for a Required Verification level."""
    directory = root / TEMPLATES_DIR
    templates = sorted(path for path in directory.glob("*.yml") if path.name not in TEMPLATE_EXEMPT)
    found: list[str] = []
    for path in templates:
        if not _VERIFICATION_FIELD.search(path.read_text(encoding="utf-8")):
            found.append(
                f"{path.relative_to(root)}: no field with id 'verification' — every "
                "issue template asks for a Required Verification level (POLICY 18)"
            )
    return found, len(templates)


def title_gate_violations(root: Path) -> list[str]:
    """Ways the PR title gate in titles.yml could have been unwired."""
    workflow = root / TITLES_WORKFLOW
    text = workflow.read_text(encoding="utf-8")
    found: list[str] = []
    if SHARED_TITLE_ACTION not in text:
        found.append(
            f"{TITLES_WORKFLOW}: the shared conventional-title action is gone — the "
            "title rule is no longer parsed by the series' one parser (POLICY 2.1.3)"
        )
    if _FAILING_STEP not in text:
        found.append(
            f"{TITLES_WORKFLOW}: no step exits non-zero on an invalid title — a bad "
            "title no longer fails the `PR title` check"
        )
    return found


def main(argv: list[str] | None = None) -> int:
    """Run both checks. Returns 0 when every gate is wired, 1 otherwise."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    root: Path = parser.parse_args(argv).root.resolve()

    missing: list[str] = []
    directory = root / TEMPLATES_DIR
    workflow = root / TITLES_WORKFLOW
    if not directory.is_dir():
        missing.append(f"{directory} does not exist, so nothing was checked")
    if not workflow.is_file():
        missing.append(f"{workflow} does not exist, so nothing was checked")
    if missing:
        for line in missing:
            print(f"  {line}", file=sys.stderr)
        return 1

    template_problems, template_count = template_violations(root)
    if template_count == 0:
        print(
            f"  {directory} holds no issue template, so nothing was checked",
            file=sys.stderr,
        )
        return 1

    problems = template_problems + title_gate_violations(root)

    if problems:
        print("A governance gate adopted in #3 has been unwired.\n", file=sys.stderr)
        for line in problems:
            print(f"  {line}", file=sys.stderr)
        print(
            "\nPOLICY 18.2: a rule without a gate is a wish. Rewire the gate, or change"
            "\nthe rule the way POLICY says rules change — never by quiet removal.",
            file=sys.stderr,
        )
        return 1

    print(
        f"Governance gates wired: {template_count} issue templates ask for a Required "
        "Verification level, and the PR title check still fails on invalid titles"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
