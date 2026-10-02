# KPubData Watch

**Can this public data be trusted and used right now?**

> A public data reliability service that continuously observes Korean public data APIs and
> publishes their current state and their change and anomaly history, with evidence. It runs
> on KPubData and does not depend on KPubData Builder.
>
> Related projects:
>
> - [KPubData](https://github.com/yeongseon/kpubdata) — a standalone Python SDK for Korean public data; the only product Watch depends on
> - [KPubData Builder](https://github.com/yeongseon/kpubdata-builder) — a sibling product that builds reproducible datasets and tables with KPubData
> - [KPubData Studio](https://github.com/yeongseon/kpubdata-studio) — a visual workspace for KPubData Builder

[한국어](./README.md)

## 무엇을 해결하나

A successful public API request does not mean the data is healthy. With `HTTP 200` the data
may not have been updated for three days, the record count may have dropped to 60% of normal,
or a field may have disappeared.

```text
HTTP 200  ≠  Data Healthy
```

KPubData Watch observes **Freshness, Contract and Quality**, not only availability, and every
verdict records Expected, Observed, Difference, Rule, Evidence and Timestamp. It never answers
"the AI decided this looks wrong".

## 현재 상태

**MVP — Public Status (0–3 months), in preparation.** The repository skeleton and CI exist;
there is no implementation yet. The MVP goal is to observe 10 real public datasets from at
least 3 providers continuously. The implementation order and the definition of done are in the
[ROADMAP](docs/ROADMAP.md).

## 문서

| Document | Contents |
|---|---|
| [PRD](docs/PRD.md) | Product definition, problem, principles, goals, non-goals, success metrics |
| [ROADMAP](docs/ROADMAP.md) | MVP scope (P0/P1/deferred), implementation order, definition of done, later phases |
| [DOMAIN_MODEL](docs/DOMAIN_MODEL.md) | Health, Check, Detection, Change, Incident |
| [Detectors](docs/detectors/README.md) | Availability, Freshness, Contract, Quality |
| [ARCHITECTURE](docs/architecture/README.md) | Probe, Observation, Scheduler, storage and deployment |
| [REGISTRY](docs/REGISTRY.md) | Dataset registry format and dataset selection |
| [UI](docs/UI.md) | UI strategy, UI Lab, Public Status screen principles |
| [TESTING](docs/TESTING.md) | Test strategy and CI gates |
| [Decisions](docs/decisions/README.md) | ADRs, mapped to the PRD decision log (D-001–D-020) |
| [API_CONTRACT](API_CONTRACT.md) | Public read API and operator CLI (draft) |
| [SECURITY](SECURITY.md) | Reporting, credential and redaction requirements |
| [CONTRIBUTING](CONTRIBUTING.md) · [AGENTS](AGENTS.md) | How to contribute, and the rules for agents |

The canonical project-management rules are kpubdata's
[POLICY.md](https://github.com/yeongseon/kpubdata/blob/main/docs/governance/POLICY.md).

## 제품군

| Repository | Role |
|---|---|
| [kpubdata](https://github.com/yeongseon/kpubdata) | Public data collection and normalisation SDK — the only product Watch depends on |
| [kpubdata-builder](https://github.com/yeongseon/kpubdata-builder) | Dataset pipeline and publishing — a sibling of Watch, not a dependency |
| [kpubdata-studio](https://github.com/yeongseon/kpubdata-studio) | Screens and workflow for Builder |
| **kpubdata-watch** | Public data reliability observation and Public Status — this repository |

## 라이선스

[MIT](LICENSE)
