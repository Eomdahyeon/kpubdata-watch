# 아키텍처

> 이 문서는 KPubData Watch MVP PRD(v1.0 Draft, 2026-09-30)의 §14, §15, §16, §17, §18, §19, §20, §28, §29, §30, §31, §32, §64, §65, §66, §67, §76, §77 를 목적별로 나눈 것이다. 전체 대응표는 [문서 안내](../index.md#prd) 에 있다.

## Overall Architecture

<small>PRD §30</small>

```text
                         KPubData
                            │
                            ▼
                   Dataset Registry
                            │
                            ▼
                       Scheduler
                            │
                            ▼
                      Probe Runner
                            │
                            ▼
                   Normalized Result
                            │
                            ▼
                       Observation
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
 Availability            Freshness           Contract
                                                │
                                                ▼
                                             Quality
                                       ┌────────┴────────┐
                                       ▼                 ▼
                                     Volume        Completeness

        └───────────────────┬───────────────────┘
                            │
                            ▼
                         Detection
                            │
                    ┌───────┴───────┐
                    ▼               ▼
                  Change         Incident
                    │               │
                    └───────┬───────┘
                            ▼
                          History
                            │
                            ▼
                         Read API
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
        Minimal Production UI          UI Lab
```

## Provider / Dataset / Probe Model

<small>PRD §14</small>

장기 확장성을 위해 Dataset과 Probe를 분리한다.

```text
Provider
   │
   └── Dataset
          │
          ├── Probe Definition A
          │
          └── Probe Definition B
```

사용자에게 보이는 단위는 Dataset이다.

내부적으로는 하나의 Dataset에 여러 Probe를 둘 수 있다.

MVP에서는 대부분:

```text
1 Dataset
    ↓
1 Primary Probe
```

로 시작한다.

## Probe Principle

<small>PRD §15</small>

Probe는 Dataset 전체를 복제하는 작업이 아니다.

목표:

> **Dataset의 현재 Reliability를 판단하는 데 필요한 최소 요청을 수행한다.**

잘못된 방식:

```text
매시간 전체 Dataset 다운로드
```

권장:

```text
Representative request
+
Metadata
+
Small sample
+
Provider total count if available
```

예:

```text
서울
page=1
rows=100
```

등 안정적인 query를 Registry에서 고정한다.

## Probe Pipeline

<small>PRD §16</small>

```text
Dataset Registry
      ↓
Scheduler
      ↓
Probe Runner
      ↓
KPubData / Provider Adapter
      ↓
Normalized Probe Result
      ↓
Observation
      ↓
Checks / Detectors
```

Provider-specific response를 Detector가 직접 다루지 않는다.

## Probe Result

<small>PRD §17</small>

표준 형태:

```python
ProbeResult(
    dataset_id="visitkorea-tourism",
    probe_id="primary",

    started_at=...,
    completed_at=...,

    success=True,

    http_status=200,
    latency_ms=812,

    record_count=100,
    total_record_count=254832,

    latest_data_at=...,

    schema={...},
    schema_hash="sha256:...",

    sample_hash="sha256:...",

    quality_metrics={
        "null_ratio.addr1": 0.012
    },

    error=None,
)
```

## Observation

<small>PRD §18</small>

Watch의 핵심 Persistent Entity다.

```text
Dataset
   │
   ├── Observation t1
   ├── Observation t2
   ├── Observation t3
   └── Observation t4
```

최소 필드:

```text
id

dataset_id
probe_id

started_at
completed_at

probe_status

http_status
latency_ms

record_count
total_record_count

latest_data_at

schema_hash
sample_hash

quality_metrics

error_category
error_message

created_at
```

## Raw Data Storage Policy

<small>PRD §19</small>

기본적으로 API 전체 Response를 장기 저장하지 않는다.

저장:

```text
Status
Timing
Count
Freshness Timestamp
Schema
Schema Hash
Sample Hash
Quality Metrics
Detection Evidence
```

저장하지 않음:

```text
전체 Raw Dataset
전체 Response Body
API Key
Authorization Header
Sensitive Query Parameters
```

필요하다면 향후 Debug Sample을:

```text
Short TTL
Explicit Opt-in
Sanitized
```

방식으로 도입한다.

MVP P0에서는 필요하지 않다.

## Schema Snapshot

<small>PRD §20</small>

Schema는 canonical representation으로 변환한다.

예:

```text
root.items[].addr1:string
root.items[].addr2:string
root.items[].contentid:string
root.items[].modifiedtime:string
```

정렬 후 Hash:

```text
SHA256(canonical_schema)
```

매 Observation마다 Schema 전체를 중복 저장하지 않는다.

```text
Observation #1 → schema A
Observation #2 → schema A
Observation #3 → schema A
Observation #4 → schema B
```

저장:

```text
SchemaSnapshot A
SchemaSnapshot B
```

## Scheduling

<small>PRD §28</small>

모든 Dataset을 같은 빈도로 호출하지 않는다.

예:

```text
Realtime / near-real-time
15~30 min

Hourly
1 hour

Daily
4~6 hours

Weekly / Monthly
1 day
```

실제 schedule은 다음을 고려한다.

```text
Official update frequency
Provider rate limit
Traffic policy
Data characteristics
Monitoring value
```

## Scheduler Architecture

<small>PRD §29</small>

MVP에서는 Distributed Scheduler를 만들지 않는다.

기본:

```text
watch-web

watch-worker
  ├── scheduler
  └── probes
```

동일 Container Image를 사용하고 실행 Command만 분리할 수 있다.

초기에는:

```text
Single Scheduler Process
+
Database-backed state
```

면 충분하다.

수천 Dataset을 위한 Kafka/Celery architecture는 MVP에서 만들지 않는다.

## Database Model

<small>PRD §66 · ADR 0011 (#35)</small>

MVP 최소 Table:

```text
providers

datasets

probe_definitions

observations

schema_snapshots

detections

changes

incidents

notices

notice_links
```

관계:

```text
Provider
   │
   └── Dataset
          │
          ├── ProbeDefinition
          │      │
          │      └── Observation
          │             │
          │             └── Detection
          │
          ├── SchemaSnapshot
          │
          ├── Change
          │
          └── Incident

Notice N:N Incident (notice_links)
Notice N:N Change   (notice_links)
```

`notices` 는 Dataset 에 속하지 않는 독립 엔티티다(공지 하나가 여러 Dataset 에
걸칠 수 있다). `notice_links` 는 `(notice_id, target_type, target_id)` 로
Incident 와 Change 에 N:N 링크한다 — Incident 의 `official_notice_url` 필드는
이 Table 로 대체됐다(ADR 0011).

## Retention

<small>PRD §67</small>

MVP 기본:

```text
Public history
30 days minimum

Internal metadata history
90 days minimum
```

실제 비용을 측정하면서 조정한다.

Schema Snapshot / Change / Incident는 가능한 한 장기 보관한다.

전체 Raw Response는 장기 보관하지 않는다.

## Monitoring Reliability

<small>PRD §64</small>

Watch 자체 상태와 Dataset 상태를 분리한다.

예:

```text
Probe was not executed
```

는:

```text
Dataset Outage
```

가 아니다.

대신:

```text
Monitoring State
UNKNOWN
```

이다.

필요한 내부 상태:

```text
Scheduler last run

Worker last heartbeat

Latest successful probe execution

Probe backlog

DB health
```

## Watch Internal Observability

<small>PRD §65</small>

최소 Metric:

```text
probe_runs_total

probe_success_total

probe_failure_total

probe_duration_seconds

detection_runs_total

incidents_open_total

incidents_resolved_total

scheduler_delay_seconds

last_successful_probe_timestamp
```

Structured Log에는 다음 Correlation ID를 포함한다.

```text
dataset_id
probe_id
observation_id
detection_id
incident_id
```

## Repository Structure

<small>PRD §31</small>

초기에는 하나의 Repository로 운영한다.

```text
kpubdata-watch/
│
├── src/
│   └── kpubdata_watch/
│       │
│       ├── registry/
│       │
│       ├── probes/
│       │
│       ├── scheduler/
│       │
│       ├── observations/
│       │
│       ├── health/
│       │
│       ├── detectors/
│       │   ├── availability/
│       │   ├── freshness/
│       │   ├── contract/
│       │   └── quality/
│       │       ├── volume/
│       │       └── completeness/
│       │
│       ├── changes/
│       ├── incidents/
│       ├── history/
│       │
│       ├── api/
│       │   ├── routes/
│       │   ├── schemas/
│       │   └── read_models/
│       │
│       ├── web/
│       │   ├── templates/
│       │   └── static/
│       │
│       ├── storage/
│       └── cli/
│
├── ui-lab/
│   ├── fixtures/
│   ├── status-page/
│   ├── provider-grouped/
│   └── issues-first/
│
├── migrations/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── fixtures/
│   ├── replay/
│   └── live/
│
├── docs/
│   ├── architecture/
│   ├── detectors/
│   └── decisions/
│
├── pyproject.toml
└── README.md
```

## Technology Recommendation

<small>PRD §32</small>

Reference implementation:

```text
Python 3.12+

FastAPI
Pydantic

SQLAlchemy
Alembic

PostgreSQL

httpx

APScheduler
or equivalent lightweight scheduler

Jinja2

HTMX optional

pytest
ruff
mypy
```

MVP에서는 별도 React/Next.js frontend를 만들지 않는다.

## Deployment

<small>PRD §77</small>

논리적으로 두 Process:

```text
watch-web

watch-worker
```

동일 Image 사용 가능.

예:

```text
Web
FastAPI + Templates + Read API

Worker
Scheduler + Probe + Detector
```

Database:

```text
PostgreSQL
```

## Non-Functional Requirements

<small>PRD §76</small>

### Performance

Public Status:

```text
P95 < 1 second
```

Public Read API:

```text
P95 < 500 ms
```

필요하면 Read Model / Cache를 사용한다.

---

### Scale Target

MVP 설계 목표:

```text
10
 ↓
30
 ↓
50
 ↓
150 Dataset
```

실제 MVP 운영은 10개로 시작하지만 UI/Data Model은 150개까지 자연스럽게 확장되는지 확인한다.

수천 개 Dataset용 Distributed Infrastructure는 만들지 않는다.
