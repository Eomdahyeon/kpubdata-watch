# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- The `PR title` check reads the title live from the API and applies kpubdata's pull-request rules — English, no issue reference or URL, at most 100 characters (kpubdata#741, #742); GitHub's `Revert "…"` title is exempt. A required check that failed no longer stays blocking once a later run of it passes: `required-check-refresh.yml` re-runs the stale failed runs of `R3 review` and `Titles` on the same head (kpubdata#759). AGENTS.md and the PR template say commit titles (= PR titles) are English and commit bodies (= PR bodies) are free, since the squash body is now the PR body (kpubdata#743).

### Added

- The MVP PRD, split by purpose: `docs/PRD.md` (the product), `docs/ROADMAP.md` (scope, order, definition of done, epics, open questions), `docs/DOMAIN_MODEL.md`, `docs/detectors/`, `docs/architecture/`, `docs/REGISTRY.md`, `docs/UI.md`, `docs/TESTING.md`, `API_CONTRACT.md` and `SECURITY.md` in English, and six ADRs in `docs/decisions/` covering decisions D-001 to D-020. `docs/index.md` maps every PRD section to the document that now holds it. Epics and open questions are GitHub issues.
- The repository, set up the same way as the KPubData series: squash-only merges with the pull request title as the commit title, the aggregate `CI gate` as the one required check, the series' label set, secret scanning with push protection, Conventional-Commit titles checked on pull requests and turned into `type:*` labels on issues, and the release workflow with the series' release-window gate.
- The package skeleton from the PRD's repository structure (`src/kpubdata_watch/`), with a `kpubdata-watch --version` command and smoke tests. Nothing is implemented yet.
- `scripts/check_independence.py` fails CI when Watch imports or declares KPubData Builder or KPubData Studio (PRD D-016); its tests plant each kind of violation and expect a failure.
- Every issue template now asks for a **Required Verification** level (V0–V5, kpubdata POLICY 18), and `scripts/check_governance.py` fails CI when a template stops asking or when `titles.yml` stops calling the series' shared conventional-title action with a failing step — the title and verification rules adopted in #3 keep their gates, and CONTRIBUTING.md documents the rule.
- **R3 review gate** (#46, kpubdata-builder#905): a pull request labelled `review:R3` now needs an approval from someone other than its author, with write access, before it can merge. The `R3 review` workflow calls kpubdata's `.github/actions/r3-review@main` on every pull request (passing when it is not R3) and again on label changes, pushes and review submissions or dismissals, with `pull-requests: read` only. An approval followed by a request for changes, a dismissed one, the author's own and a bot's do not count; one on an older head does, as branch protection's stale-approval dismissal is off. `R3 review` becomes a required status check; the approval count in branch protection stays at 0.

### Security

- **`Secret scan (gitleaks)` no longer fails on another branch's commits** (#50). Without `--log-opts`, gitleaks runs `git log --all`, which — combined with `fetch-depth: 0` pulling in every remote branch — walked unmerged PR branches too, so a synthetic test key on someone else's open branch turned this job, which `CI gate` needs, red for runs that never touched that branch. The job now scopes `--log-opts` to the run's own commits: a pull request scans `base..head`, a push to `main` scans `before..sha` (or just `sha` for a brand-new branch, where `before` is all zeros), and `schedule`/`workflow_dispatch` scan the default branch's full history only — never another branch. `.gitleaksignore` is unaffected. Ported from kpubdata-studio#685/#686.
