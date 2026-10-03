# API Contract — KPubData Watch

> **Status: draft.** This is the MVP read API and operator CLI from the PRD
> (§56–§60), translated faithfully. Nothing here is implemented yet (#38 for the
> read API, #5/#6/#36 for the CLI commands). Until an implementation and a
> machine-checked contract exist, field names and shapes may change.

The read API serves read models, never database tables ([docs/UI.md](docs/UI.md),
"UI Architecture"). Every UI — the production status pages and the UI Lab —
consumes these endpoints.

## Conventions

- Base path: `/api/v1`.
- Timestamps are ISO 8601. The examples use UTC (`Z`) and KST (`+09:00`) offsets.
- `health` is one of `healthy`, `degraded`, `critical`, `unknown`.
- The four checks are `availability`, `freshness`, `contract`, `quality`.
- A check result is one of `pass`, `warn`, `fail`, `unknown`, `not_applicable`.
- Credentials never appear in any response ([SECURITY.md](SECURITY.md)).

## GET `/api/v1/health`

<small>PRD §56</small>

The health summary across every monitored dataset.

```json
{
  "generated_at": "2026-09-30T12:00:00Z",

  "summary": {
    "healthy": 9,
    "degraded": 1,
    "critical": 0,
    "unknown": 0
  }
}
```

## GET `/api/v1/datasets`

<small>PRD §57</small>

Filter candidates:

```text
provider
health
check
category
q
```

`items` holds one entry per dataset, in the same shape as
`GET /api/v1/datasets/{id}` below. `name` and `provider.name` are display values
and stay in Korean.

```json
{
  "generated_at": "2026-10-02T21:15:00+09:00",
  "items": [ … ]
}
```

## GET `/api/v1/datasets/{id}`

<small>PRD §58 · #82</small>

Each check carries its result and, when it is not a plain pass, a one-line
`summary`. `last_successful_at` is the last probe that got a response,
`last_healthy_at` the last observation in which the dataset was Healthy, and
`latest_data_at` the newest data the provider has published (absent when it cannot
be known). Active incidents and the latest changes are embedded as summaries; their
details have their own endpoints.

```json
{
  "id": "datago.apt_rent",
  "name": "아파트 전월세 실거래가",
  "provider": {
    "id": "molit",
    "name": "국토교통부"
  },
  "category": "real-estate",
  "health": "critical",
  "checks": {
    "availability": {
      "status": "pass",
      "summary": null
    },
    "freshness": {
      "status": "pass",
      "summary": null
    },
    "contract": {
      "status": "fail",
      "summary": "필드 1개 삭제 (breaking)"
    },
    "quality": {
      "status": "pass",
      "summary": null
    }
  },
  "last_checked_at": "2026-10-02T21:14:40+09:00",
  "last_successful_at": "2026-10-02T21:14:40+09:00",
  "last_healthy_at": "2026-10-02T20:42:00+09:00",
  "latest_data_at": null,
  "active_incidents": [
    {
      "id": "inc-contract-apt-rent-001",
      "dataset_id": "datago.apt_rent",
      "check": "contract",
      "severity": "critical",
      "status": "ongoing",
      "title": "Breaking contract change",
      "summary": "응답에서 필드 addr2가 사라졌습니다.",
      "started_at": "2026-10-02T21:03:00+09:00",
      "detected_at": "2026-10-02T21:03:00+09:00",
      "confirmed_at": "2026-10-02T21:05:00+09:00",
      "resolved_at": null
    }
  ],
  "latest_changes": [
    {
      "id": "chg-contract-apt-rent-001",
      "dataset_id": "datago.apt_rent",
      "change_type": "contract",
      "severity": "critical",
      "title": "Contract changed",
      "summary": "필드 addr2가 삭제됐습니다.",
      "detected_at": "2026-10-02T21:03:00+09:00"
    }
  ]
}
```

## History API

<small>PRD §59 · ADR 0010 (#32)</small>

```text
GET /api/v1/datasets/{id}/history

GET /api/v1/incidents

GET /api/v1/incidents/{id}

GET /api/v1/changes

GET /api/v1/changes/{id}
```

The dataset history accepts `days` — default `30` (the public-history retention
floor), capped at `90` (the internal-metadata floor). A request above the cap is
served at the cap, and the response reports both `requested_days` and
`effective_days`. Change and incident listings carry no period limit: those
entities are kept as long as possible.

`GET /api/v1/datasets/{id}/history` returns one Health per day, oldest first:

```json
{
  "dataset_id": "datago.apt_rent",
  "requested_days": 30,
  "effective_days": 30,
  "days": [
    {
      "date": "2026-09-03",
      "health": "healthy",
      "summary": null
    },
    …,
    {
      "date": "2026-10-02",
      "health": "critical",
      "summary": "Breaking contract change"
    }
  ]
}
```

`GET /api/v1/incidents/{id}` returns the incident with its evidence (PRD §22:
expected, observed, difference, rule) and its observation timeline. `status` is one
of `open`, `ongoing`, `resolved`, `false_positive`; `severity` one of `info`,
`warning`, `critical`.

```json
{
  "id": "inc-contract-apt-rent-001",
  "dataset_id": "datago.apt_rent",
  "check": "contract",
  "severity": "critical",
  "status": "ongoing",
  "title": "Breaking contract change",
  "summary": "응답에서 필드 addr2가 사라졌습니다.",
  "started_at": "2026-10-02T21:03:00+09:00",
  "detected_at": "2026-10-02T21:03:00+09:00",
  "confirmed_at": "2026-10-02T21:05:00+09:00",
  "resolved_at": null,
  "evidence": {
    "expected": {
      "fields": [
        "addr1:string",
        "addr2:string"
      ]
    },
    "observed": {
      "fields": [
        "addr1:string"
      ]
    },
    "difference": {
      "removed": [
        "addr2:string"
      ]
    },
    "rule": {
      "id": "contract.field_removed",
      "description": "A field present in the accepted schema was removed"
    },
    "first_seen_at": "2026-10-02T21:03:00+09:00",
    "confirmed_at": "2026-10-02T21:05:00+09:00"
  },
  "timeline": [
    {
      "at": "2026-10-02T20:42:00+09:00",
      "summary": "마지막 Healthy 관측"
    },
    {
      "at": "2026-10-02T21:03:00+09:00",
      "summary": "필드 addr2 삭제 관측"
    },
    {
      "at": "2026-10-02T21:05:00+09:00",
      "summary": "Breaking contract change 확인 (Critical)"
    }
  ],
  "related_change_id": "chg-contract-apt-rent-001"
}
```

`GET /api/v1/changes/{id}` returns the change with a human-readable diff in
`name:type` form and its effect on Health (`health_impact`: `none`, `degraded`,
`critical`). A Change is an observed fact, not necessarily a problem: an additive
change has `health_impact: "none"` and no related incident.

```json
{
  "id": "chg-contract-apt-rent-001",
  "dataset_id": "datago.apt_rent",
  "change_type": "contract",
  "severity": "critical",
  "title": "Contract changed",
  "summary": "필드 addr2가 삭제됐습니다.",
  "detected_at": "2026-10-02T21:03:00+09:00",
  "diff": {
    "added": [],
    "removed": [
      "addr2:string"
    ],
    "changed": []
  },
  "health_impact": "critical",
  "related_incident_id": "inc-contract-apt-rent-001"
}
```

## Operator CLI

<small>PRD §60</small>

The MVP has no separate admin web application; the CLI is enough.

```bash
kpubdata-watch datasets list

kpubdata-watch dataset show visitkorea-tourism

kpubdata-watch probe visitkorea-tourism

kpubdata-watch probe --all

kpubdata-watch incidents list

kpubdata-watch incidents resolve <id>

kpubdata-watch incidents false-positive <id>

kpubdata-watch notices add <url> [--title ...] [--excerpt ...]

kpubdata-watch notices link <notice-id> --incident <id> | --change <id>
```

Today only `kpubdata-watch --version` exists. Notices are their own entity and
link many-to-many to incidents and changes (ADR 0011, #35); linking is
informational and never resolves an incident.

## Read model the UIs share

<small>PRD §35 — see [docs/UI.md](docs/UI.md) · #82</small>

The shapes above are defined once, as pydantic models in
`src/kpubdata_watch/api/read_models/public.py`, and every UI renders from them. The
fixture demo stores one complete snapshot as five files in `demo/fixtures/`
(`snapshot`, `datasets`, `incidents`, `changes`, `histories`);
`ProductSnapshot` (`read_models/snapshot.py`) loads them and rejects any reference
that does not resolve or that disagrees with what it points at: a dataset's
`active_incident_ids` are exactly its `open` and `ongoing` incidents, and an
incident's `related_change_id` and a change's `related_incident_id` name each
other (#107). Timestamps are stored, never relative times such as
"3m ago": a page computes what it shows from `generated_at`.

## Performance targets

<small>PRD §76</small>

| Surface | Target |
|---|---|
| Public status pages | P95 < 1 second |
| Public read API | P95 < 500 ms |

Read models or a cache are used when needed.
