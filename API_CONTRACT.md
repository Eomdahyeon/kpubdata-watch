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

Example:

```json
{
  "items": [
    {
      "id": "visitkorea-tourism",

      "name": "한국관광공사 관광정보",

      "provider": "한국관광공사",

      "health": "healthy",

      "last_checked_at": "...",

      "active_issue": null
    }
  ]
}
```

`name` and `provider` are display values and stay in Korean.

## GET `/api/v1/datasets/{id}`

<small>PRD §58</small>

```json
{
  "id": "visitkorea-tourism",

  "health": "healthy",

  "checks": {
    "availability": "pass",
    "freshness": "pass",
    "contract": "pass",
    "quality": "pass"
  },

  "last_checked_at": "...",

  "latest_data_at": "...",

  "latest_schema_hash": "..."
}
```

## History API

<small>PRD §59</small>

```text
GET /api/v1/datasets/{id}/history

GET /api/v1/incidents

GET /api/v1/incidents/{id}

GET /api/v1/changes

GET /api/v1/changes/{id}
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

kpubdata-watch incidents add-notice <id> <url>
```

Today only `kpubdata-watch --version` exists.

## Read model the UIs share

<small>PRD §35 — see [docs/UI.md](docs/UI.md)</small>

```json
{
  "dataset_id": "visitkorea-tourism",

  "name": "한국관광공사 관광정보",
  "provider": "한국관광공사",

  "health": "healthy",

  "checks": {
    "availability": "pass",
    "freshness": "pass",
    "contract": "pass",
    "quality": "pass"
  },

  "active_issue": null,

  "latest_change": {
    "type": "contract",
    "severity": "info",
    "occurred_at": "2026-09-29T14:20:00+09:00"
  },

  "last_checked_at": "2026-09-30T21:10:00+09:00"
}
```

## Performance targets

<small>PRD §76</small>

| Surface | Target |
|---|---|
| Public status pages | P95 < 1 second |
| Public read API | P95 < 500 ms |

Read models or a cache are used when needed.
