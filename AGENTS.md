# AGENTS.md — kpubdata-watch

> **[POLICY.md](https://github.com/kpubdata-lab/kpubdata/blob/main/docs/governance/POLICY.md)
> is the single canonical source for project-management and review policy.** Epic,
> Issue, Priority, Review Level, Verification and Release rules come from there.
> This file keeps only what is specific to this repository. POLICY.md wins any conflict.

## Mission

Implement KPubData Watch: a public data reliability service that observes Korean
public data APIs and answers **"Can this public data be trusted and used right
now?"** — with evidence. The MVP is **Public Status** ([docs/PRD.md](docs/PRD.md)).

## Ground rules

These come from the PRD's principles: **Simple, Explainable, Reproducible,
Evidence-based.**

- Every detection records **Expected, Observed, Difference, Rule, Evidence and
  Timestamp**. "The AI decided this looks wrong" is never an acceptable result.
- **One health per dataset; many checks.** Do not add a new "X Health". A new
  signal is a check or a metric ([docs/DOMAIN_MODEL.md](docs/DOMAIN_MODEL.md)).
- **A change is not a problem.** An informational change never lowers health.
- **Watch's own failure is not a provider outage.** If Watch could not observe,
  the answer is `UNKNOWN`, never `CRITICAL`.
- **MVP detection is rule- and baseline-based.** No ML, no learned seasonality.
- **Detectors never read provider-specific responses.** They read the normalised
  probe result.
- **No full raw responses stored long-term, and no credentials anywhere** — not in
  Git, the database, logs, incident evidence, the public API or HTML
  ([SECURITY.md](SECURITY.md)).
- **Watch depends on KPubData only.** Never import or declare `kpubdata_builder` or
  `kpubdata_studio` (PRD D-016); `scripts/check_independence.py` enforces it.
- **UI layout is not fixed; the read model is.** UIs consume the read API, never
  database tables ([docs/UI.md](docs/UI.md)).

When a feature's place is unclear, ask the PRD's boundary question: *without it,
can Public Status still discover a real anomaly in public data and explain why?*
If it can, the feature goes to the backlog.

## Language policy

> [kpubdata ADR 0003](https://github.com/kpubdata-lab/kpubdata/blob/main/docs/adrs/0003-language-policy.md)
> is canonical.

| Area | Language |
|---|---|
| Code identifiers, comments, docstrings | English |
| Commit titles (= PR titles), issue titles, CHANGELOG | English |
| Commit bodies (= PR bodies) | Korean or English — the squash body is the PR body ([POLICY 2.1.3](https://github.com/kpubdata-lab/kpubdata/blob/main/docs/governance/POLICY.md), kpubdata#743) |
| Governance documents (`AGENTS.md`, `CONTRIBUTING.md`) | English |
| Implementation contracts (`API_CONTRACT.md`, `SECURITY.md`) | English |
| Design rationale (PRD, ARCHITECTURE, DOMAIN_MODEL, detectors, UI, ADRs) | Korean |
| README | Korean first, with `README.en.md` kept at parity |
| Issue bodies, PR bodies, review comments | Korean or English |

`scripts/check_english_comments.py` fails CI on a Korean comment or docstring.
`scripts/check_readme_parity.py` fails CI when the two READMEs' sections differ.

## Verification is done by machines

[POLICY 18.2](https://github.com/kpubdata-lab/kpubdata/blob/main/docs/governance/POLICY.md)
and [VERIFICATION.md](https://github.com/kpubdata-lab/kpubdata/blob/main/docs/governance/VERIFICATION.md)
are canonical.

- **A sentence with a number in it comes from a command.** Paste the output.
- **Sweep with `git ls-files`, not with paths you chose.**
- **A rule without a gate is a wish.** Add the check, wire it into CI, and write the
  test that shows it failing.
- **Branch protection requires only the aggregate `CI gate` job.** Never require a
  matrix-suffixed name: an absent required check blocks every pull request for ever.

## Labels — what an agent applies

POLICY 2.1, 2.1.1 and 2.1.2 are the label reference. What is specific to agents:

- A new issue carries **at least one `epic:*`**. Its title starts with a
  Conventional Commits type, and the `type:*` label follows from the title
  (POLICY 2.1.3). **Never set `type:*` by hand.**
- Pull request titles use the same types; the `PR title` check fails otherwise.
- No issue numbers in titles. They go in the body (`Closes #N`).
- Leave Priority off when there is no evidence for it.
- A pull request labelled `review:R3` cannot merge until someone other than its
  author, with write access, approves it: the required `R3 review` check fails until
  then (kpubdata POLICY 14.1). The author's own approval, a bot's, and one followed by
  a request for changes do not count. Ask for the review; do not remove the label.
- Do not create labels POLICY does not list, lower a `review:*` level, or promote to
  `priority:high`/`priority:critical`.

## Branch rules

- The default branch is `main`. **Never push to `main` directly** — branch
  protection refuses it.
- Branch names: `feat/issue-<number>-<short-description>`,
  `fix/issue-<number>-<short-description>`, `docs/<short-description>`.
- Squash merge only; the pull request title becomes the commit title.
- If a git operation is not obviously safe, **ask instead of guessing.**

## Releases

Cadence lives in
[kpubdata's compatibility.md §5.1](https://github.com/kpubdata-lab/kpubdata/blob/main/docs/compatibility.md#release-cadence);
who may do what lives in POLICY 14.

- **Watch's cadence is not decided yet** (on demand like kpubdata, or monthly like
  Builder and Studio). Until it is, `release.yml` uses the `monthly` release window.
- **Prepare, do not release.** An agent may tidy the CHANGELOG's `[Unreleased]`
  section and run the release workflow with `dry_run`. Pushing a tag, creating a
  GitHub Release and approving a deployment are a person's.
- **Write what a change does under `## [Unreleased]` in `CHANGELOG.md` as you merge it.**
- **Never recommend a release outside the rule to unblock work.**

## Build order

The PRD's recommended implementation order ([docs/ROADMAP.md](docs/ROADMAP.md)):

1. Repository / CI
2. Dataset registry
3. Probe runtime
4. Observation
5. Availability
6. Contract diff
7. Freshness
8. Quality (volume, completeness)
9. Detection / change / incident
10. Health aggregation
11. Read API
12. Minimal public status
13. UI Lab (10 / 50 / 150 datasets)
14. 10 real datasets
15. History accumulation
16. Real incident / change replay
17. Production hardening

Do not stop the observation engine waiting for UI decisions, and do not invent UI
data shapes because the backend came first: the connection point is
**domain → stable read model → experimental UI**.

## Test expectations

- Unit tests for every detector, the health aggregator, change classification, the
  incident lifecycle and secret redaction.
- Fixture regression tests for each detector outcome (`tests/fixtures/`).
- Replay tests that preserve real before/after API changes (`tests/replay/`).
- Integration tests of the whole pipeline against a mock HTTP server.
- Live tests only with real credentials, marked `live`; never in PR CI.

Details: [docs/TESTING.md](docs/TESTING.md).

## Directory layout

```text
src/kpubdata_watch/
├── registry/        # version-controlled dataset registry (YAML)
├── probes/          # probe runner through KPubData
├── scheduler/       # single-process scheduler, database-backed state
├── observations/    # observation storage
├── health/          # one health per dataset
├── detectors/       # availability, freshness, contract, quality/{volume,completeness}
├── changes/         # immutable observed facts
├── incidents/       # problems with a lifecycle
├── history/
├── api/             # routes, schemas, read_models
├── web/             # minimal server-rendered UI (templates, static)
├── storage/
└── cli/             # operator commands
ui-lab/              # disposable UI experiments on the same read model
showcase/            # showcase project (placeholder)
migrations/          # Alembic
tests/               # unit, integration, fixtures, replay, live
docs/                # PRD, ROADMAP, DOMAIN_MODEL, ARCHITECTURE, detectors, UI, decisions
```

## Before handing work back

- [ ] `uv run ruff check .` and `uv run ruff format --check .` pass
- [ ] `uv run mypy src` passes
- [ ] `uv run pytest` passes
- [ ] A new detector explains its verdict with evidence and has fixture tests
- [ ] No credential can reach a log, the database, the API or HTML
- [ ] `CHANGELOG.md` `[Unreleased]` says what changed

## Related documents

| Document | What it covers |
|---|---|
| [docs/PRD.md](docs/PRD.md) | The product |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Scope, order and definition of done |
| [docs/DOMAIN_MODEL.md](docs/DOMAIN_MODEL.md) | Health, checks, changes, incidents |
| [docs/architecture/README.md](docs/architecture/README.md) | Pipeline, storage, deployment |
| [docs/decisions/README.md](docs/decisions/README.md) | Decisions |
| [API_CONTRACT.md](API_CONTRACT.md) | Read API and CLI |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute |
| [SECURITY.md](SECURITY.md) | Security policy |

### KPubData product family

| Repository | Document |
|---|---|
| [kpubdata](https://github.com/kpubdata-lab/kpubdata) | [AGENTS.md](https://github.com/kpubdata-lab/kpubdata/blob/main/AGENTS.md) |
| [kpubdata-builder](https://github.com/kpubdata-lab/kpubdata-builder) | [AGENTS.md](https://github.com/kpubdata-lab/kpubdata-builder/blob/main/AGENTS.md) |
| [kpubdata-studio](https://github.com/kpubdata-lab/kpubdata-studio) | [AGENTS.md](https://github.com/kpubdata-lab/kpubdata-studio/blob/main/AGENTS.md) |
