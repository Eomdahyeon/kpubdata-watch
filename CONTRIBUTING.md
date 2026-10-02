# Contributing to KPubData Watch

Thank you for helping. KPubData Watch observes Korean public data APIs and explains
their reliability with evidence; start with [docs/PRD.md](docs/PRD.md) for what the
product is and [docs/ROADMAP.md](docs/ROADMAP.md) for what is in scope now.

The project-management rules (labels, priority, review levels, releases) are
kpubdata's [POLICY.md](https://github.com/kpubdata-lab/kpubdata/blob/main/docs/governance/POLICY.md).

## Language

Write code, comments, docstrings, commit messages and titles in English. Issue and
pull request bodies may be Korean or English. Design documents under `docs/` are
Korean. **Do not let English block a contribution** — if a title is hard to write in
English, open it in Korean and say so; triage will help.

## Development setup

Requirements: Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/<you>/kpubdata-watch.git
cd kpubdata-watch
uv sync --extra dev
uv run pytest
```

## Checks

CI runs these; run them before you push.

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
uv run python scripts/check_english_comments.py src tests scripts
uv run python scripts/check_readme_parity.py
uv run python scripts/check_independence.py
uv run python scripts/check_governance.py
```

Live tests call real public APIs and need credentials in the environment. They are
marked `live` and never run in pull request CI:

```bash
uv run pytest -m live
```

## Branches, titles and pull requests

- Work on a branch: `feat/issue-<n>-<desc>`, `fix/issue-<n>-<desc>` or
  `docs/<desc>`. Never push to `main`.
- Titles follow Conventional Commits — `type(scope): description` — with one of
  `feat fix docs test perf refactor ci build chore style revert`. The `PR title`
  check fails otherwise, and an issue's title sets its `type:*` label.
- Put issue numbers in the body (`Closes #123`), not in the title.
- Pull requests are squash-merged, so the title becomes the commit.
- Add a line under `## [Unreleased]` in `CHANGELOG.md` for anything a user or
  operator would notice.

## Issues carry a Required Verification

Every issue states the machine verification that proves it done — V0 static
checks through V5-live product E2E, the levels of kpubdata
[POLICY.md §18](https://github.com/kpubdata-lab/kpubdata/blob/main/docs/governance/POLICY.md).
The issue templates ask for the level, and `scripts/check_governance.py` fails
CI when a template stops asking. A pull request that closes an issue meets that
level, or says why it cannot yet.

## What a good change looks like here

- A detector's verdict can be explained: Expected, Observed, Difference, Rule,
  Evidence, Timestamp ([docs/DOMAIN_MODEL.md](docs/DOMAIN_MODEL.md)).
- It comes with fixture tests, and a replay test when it reproduces a real API change.
- No credential appears in logs, the database, API responses or HTML.
- Watch still depends on KPubData only — never on KPubData Builder or Studio.

## Reporting a vulnerability

Do not open a public issue; see [SECURITY.md](SECURITY.md).
