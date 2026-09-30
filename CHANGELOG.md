# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- The MVP PRD, split by purpose: `docs/PRD.md` (the product), `docs/ROADMAP.md` (scope, order, definition of done, epics, open questions), `docs/DOMAIN_MODEL.md`, `docs/detectors/`, `docs/architecture/`, `docs/REGISTRY.md`, `docs/UI.md`, `docs/TESTING.md`, `API_CONTRACT.md` and `SECURITY.md` in English, and six ADRs in `docs/decisions/` covering decisions D-001 to D-020. `docs/index.md` maps every PRD section to the document that now holds it. Epics and open questions are GitHub issues.
- The repository, set up the same way as the KPubData series: squash-only merges with the pull request title as the commit title, the aggregate `CI gate` as the one required check, the series' label set, secret scanning with push protection, Conventional-Commit titles checked on pull requests and turned into `type:*` labels on issues, and the release workflow with the series' release-window gate.
- The package skeleton from the PRD's repository structure (`src/kpubdata_watch/`), with a `kpubdata-watch --version` command and smoke tests. Nothing is implemented yet.
- `scripts/check_independence.py` fails CI when Watch imports or declares KPubData Builder or KPubData Studio (PRD D-016); its tests plant each kind of violation and expect a failure.
