# 로드맵 — MVP 범위와 이후 단계

> 이 문서는 KPubData Watch MVP PRD(v1.0 Draft, 2026-09-30)의 §78, §79, §80, §81–93, §94, §97, §98, §99, §100, §105, §106 를 목적별로 나눈 것이다. 전체 대응표는 [문서 안내](index.md#prd) 에 있다.

## MVP Functional Scope

<small>PRD §78</small>

### P0 — 반드시 구현

```text
Dataset Registry

Provider / Dataset model

Probe Runner

Scheduler

Observation storage

Availability Check

Freshness Check

Contract Diff

Quality / Volume

Quality / Completeness

Health Aggregation

Change model

Incident model

Incident lifecycle

Schema history

Public Read API

Minimal Public Status

Dataset Detail

Incident Detail

History

Secret Redaction

Mock-based E2E Tests

Live Smoke Tests

UI Lab
```

## P1 — 시간이 허용하면

<small>PRD §79</small>

```text
Official Notice manual linking

Latency Trend

Small Sparklines

RSS / Atom Change Feed

Operator Email Alert

Provider Group View production adoption

Search / Filter UI

Response sample short TTL debugging

Basic metrics endpoint
```

## Explicitly Deferred

<small>PRD §80</small>

```text
Login

My Watchlist

BYOK

Dependency

Impact

Team

Billing

Slack / Teams

Webhook

Usage Manifest

Automatic Notice Crawling

AI Explain

AI Migration Guide

Machine-learning anomaly detection

Automatic seasonality modeling
```

## Recommended Implementation Order

<small>PRD §106</small>

최종 구현 순서는 다음을 권장한다.

```text
1. Repository / CI
        ↓
2. Dataset Registry
        ↓
3. Probe Runtime
        ↓
4. Observation
        ↓
5. Availability
        ↓
6. Contract Diff
        ↓
7. Freshness
        ↓
8. Quality
   ├─ Volume
   └─ Completeness
        ↓
9. Detection / Change / Incident
        ↓
10. Health Aggregation
        ↓
11. Read API
        ↓
12. Public UI Foundation (Brand v2 tokens, Logo/lockup, status components, theme — landed via #90–#94, #97–#104)
        ↓
13. Minimal Public Status
        ↓
14. UI Lab
    ├─ 10 datasets
    ├─ 50 datasets
    └─ 150 datasets
        ↓
15. 10 Real Datasets
        ↓
16. History Accumulation
        ↓
17. Real Incident / Change Replay
        ↓
18. Production Hardening
```

12 단계(Public UI Foundation)는 PRD 원문에 없고 #68 ([ADR 0014](decisions/0014-brand-v2-visual-identity.md)) 에서 추가했다. Minimal Public Status 와 UI Lab 이 같은 Brand v2 토큰 · lockup · 상태 컴포넌트 · theme 위에서 시작하게 하기 위해서다. 그 뒤 단계 번호는 하나씩 밀렸다. 토큰 · 로고/lockup · 상태 컴포넌트는 #90–#94, 데모 제품 화면은 #97–#104 로 이미 구현됐다.

UI 디자인 결정을 기다리느라 Observation Engine 개발을 멈추지 않는다.

동시에 Backend를 먼저 만든다는 이유로 UI에 필요한 데이터 구조를 임의로 결정하지도 않는다.

핵심 연결점은:

```text
Domain
   ↓
Stable Read Model
   ↓
Experimental UI
```

이다.

### 구현 순서와 이슈

| 순서 | 단계 | 이슈 |
|---|---|---|
| 1 | Repository / CI | #3, #4 |
| 2 | Dataset Registry | #5 |
| 3 | Probe Runtime | #6 |
| 4 | Observation | #7 |
| 5 | Availability | #8 |
| 6 | Contract Diff | #9 |
| 7 | Freshness | #10 |
| 8 | Quality (Volume · Completeness) | #11 |
| 9–10 | Detection / Change / Incident · Health Aggregation | #36 |
| 11 | Read API | #38 |
| 12 | Public UI Foundation (Brand v2 tokens, Logo/lockup, status components, theme — landed via #90–#94, #97–#104) | #68 |
| 13 | Minimal Public Status | #41 |
| 14 | UI Lab (10 / 50 / 150) | #40 |
| 15 | 10 Real Datasets | #42 |
| 16–17 | History Accumulation · Real Incident / Change Replay | #43 |
| 18 | Production Hardening | #44 |

## Definition of Done — MVP

<small>PRD §94</small>

다음을 모두 만족하면 Public Status MVP 완료로 판단한다.

```text
[ ] 10개 실제 공공 Dataset 등록

[ ] 최소 3개 Provider 포함

[ ] Dataset별 Scheduler 실행

[ ] Probe 결과 Observation 저장

[ ] Availability Check 동작

[ ] Freshness 가능한 Dataset에서 Freshness 동작

[ ] Contract Diff 동작

[ ] Volume Detection 동작

[ ] Completeness Detection 동작

[ ] Change / Incident가 분리됨

[ ] Incident Open / Resolve 동작

[ ] Dataset Health Aggregate 동작

[ ] Monitoring Failure와 Provider Failure가 분리됨

[ ] Public Status 제공

[ ] Dataset Detail 제공

[ ] Incident Detail 제공

[ ] Change History 제공

[ ] Public Read API 제공

[ ] Secret이 로그/DB/UI에 노출되지 않음

[ ] Mock E2E Test 존재

[ ] Replay Test 존재

[ ] Live Smoke Test 존재

[ ] UI Lab에서 10/50/150 Dataset 검증 가능

[ ] 실제 또는 역사적 API 변경 사례를
    End-to-End로 재현할 수 있음
```

## Development Epics

<small>PRD §81–§93</small>

PRD 의 Epic 은 GitHub 이슈로 관리한다. 아래는 PRD 원문이고, 진행 상황은 각 이슈가 정본이다.

### Epic 1 — Repository & Foundation

<small>PRD §81 · 이슈 #3, #4</small>

Deliverables:

```text
Project skeleton

Python packaging

Configuration

PostgreSQL connection

Alembic

Base logging

CI

ruff / mypy / pytest
```

Definition of Done:

```text
Application starts

Migration runs

CI green

Local development documented
```

### Epic 2 — Dataset Registry

<small>PRD §82 · 이슈 #5</small>

Deliverables:

```text
Provider model

Dataset model

ProbeDefinition model

YAML Registry loader

Validation

CLI:
datasets list
dataset show
```

DoD:

```text
Invalid configuration rejected

Version-controlled Dataset config

At least one real Dataset registered
```

### Epic 3 — Probe Runtime

<small>PRD §83 · 이슈 #6</small>

Deliverables:

```text
Probe Runner

KPubData Adapter

Timeout

Response Size Limit

Error Classification

ProbeResult

Secret Redaction
```

DoD:

```text
Real public API can be safely probed

Secrets never appear in logs

Failure categories normalized
```

### Epic 4 — Observation

<small>PRD §84 · 이슈 #7</small>

Deliverables:

```text
Observation DB Model

Observation Repository

Schema Hash

Sample Hash

Quality Metrics

History persistence
```

DoD:

```text
Repeated probes create queryable historical observations
```

### Epic 5 — Availability

<small>PRD §85 · 이슈 #8</small>

Deliverables:

```text
Transport failures

Timeout

HTTP errors

Provider error response

Credential distinction

Confirmation rules
```

DoD:

```text
Provider failure and Watch monitoring failure are distinguishable
```

### Epic 6 — Contract

<small>PRD §86 · 이슈 #9</small>

Deliverables:

```text
Schema Canonicalization

Schema Snapshot

Schema Hash

Diff Engine

Added Field

Removed Field

Type Change

Change Classification
```

DoD:

```text
Historical before/after fixture generates deterministic diff
```

### Epic 7 — Freshness

<small>PRD §87 · 이슈 #10</small>

Deliverables:

```text
Latest timestamp extractor

Expected interval

Grace period

Timezone handling

Freshness Detection

Freshness Evidence
```

DoD:

```text
Fresh and stale fixtures correctly classified
```

### Epic 8 — Quality

<small>PRD §88 · 이슈 #11</small>

Deliverables:

```text
Volume Metrics

Rolling Baseline

Completeness Metrics

Threshold configuration

Baseline-building state
```

DoD:

```text
No ML required

Detection fully explainable

Insufficient history handled safely
```

### Epic 9 — Incident & Health

<small>PRD §89 · 이슈 #36</small>

Deliverables:

```text
Detection

Change

Incident

Severity

Open / Resolve

False Positive

Health Aggregation

Flapping Protection
```

DoD:

```text
One complete failure → recovery sequence can be replayed
```

### Epic 10 — Read API

<small>PRD §90 · 이슈 #38</small>

Deliverables:

```text
Health Summary

Dataset List

Dataset Detail

History

Changes

Incidents

Filtering foundation
```

DoD:

```text
UI requires no direct DB knowledge
```

### Epic 11 — Public Status UI

<small>PRD §91 · 이슈 #41</small>

Deliverables:

```text
Minimal Status View

Dataset Detail

Incident Detail

Change Detail

Mobile-compatible layout

Accessibility basics
```

DoD:

```text
Actual monitored Dataset data visible publicly
```

### Epic 12 — UI Lab

<small>PRD §92 · 이슈 #40</small>

Deliverables:

```text
10 Dataset Fixture

50 Dataset Fixture

150 Dataset Fixture

Status-page Prototype

Provider-grouped Prototype

Issues-first Prototype
```

DoD:

```text
All prototypes consume same Read Model
```

### Epic 13 — Production Hardening

<small>PRD §93 · 이슈 #44</small>

Deliverables:

```text
10 actual datasets

3+ providers

Deployment

Internal monitoring

Structured logs

Retention

Backup

Rate control

Security review

Live smoke tests
```

## Open Questions

<small>PRD §105</small>

구현 과정에서 검증할 항목은 문서가 아니라 이슈로 관리한다.

| 질문 | 이슈 |
|---|---|
| [Q-001] 첫 10개 Dataset은 무엇으로 선정할 것인가? | #42 |
| [Q-002] Freshness를 신뢰성 있게 추출할 수 있는 Dataset은 몇 개인가? | #26 |
| [Q-003] Provider별 Rate Limit / Terms를 어떻게 Registry에 표현할 것인가? | #27 |
| [Q-004] Volume에서 totalCount와 sample count를 어떻게 구분할 것인가? | #28 |
| [Q-005] Completeness 대상 Field를 어떤 기준으로 선정할 것인가? | #29 |
| [Q-006] Breaking Contract의 기본 Severity는 어느 수준이어야 하는가? | #30 |
| [Q-007] Incident Confirmation 횟수를 Dataset별로 조정해야 하는가? | #31 |
| [Q-008] Public History 기본 기간을 30일로 둘 것인가? | #32 |
| [Q-009] Status / Provider / Issues-first 중 어떤 UI가 50~150 Dataset에서 가장 효과적인가? | #33 |
| [Q-010] 실제 Silent Data Error 사례를 최소 하나 재현 가능한 Fixture로 확보할 수 있는가? | #43 |
| [Q-011] Official Notice와 Observation을 어떤 방식으로 연결할 것인가? | #35 |
| [Q-012] Public Status가 실제 잠재 고객 유입 채널이 되는가? | #37 |
| (저장소 설정 중 추가) Watch 의 릴리스 주기 — on-demand 인가 monthly 인가 | #39 |

## Roadmap After MVP

<small>PRD §97</small>

### Phase 1 — Public Status

```text
Dataset Observation

Health

Detection

Change

Incident

History

Public Status
```

---

### Phase 2 — My Watchlist

추가 Entity:

```text
User

Watchlist

Dataset Subscription

Field Dependency

Notification Preference
```

흐름:

```text
User
  ↓
My Watchlist
  ↓
Dataset
  ↓
Field Selection
  ↓
Dependency
```

## Phase 3 — Impact

<small>PRD §98</small>

```text
Change

     +

Dataset.Field Dependency

     +

Service

     ↓

Impact
```

예:

```text
Detected

addr2 removed


Dependency

Service A
uses tourism.addr2


Impact

HIGH

Migration required
```

이 단계에서 제품 전체의:

```text
Watch → Detect → Impact
```

비전이 완성된다.

## Usage Manifest — Future

<small>PRD §99</small>

초기 Dependency는 사용자가 직접 등록한다.

향후:

```text
KPubData SDK
     ↓
Explicit user consent
     ↓
Usage Manifest
     ↓
Dataset / Field metadata
     ↓
Watch
```

원본 데이터나 개인정보는 보내지 않고 사용 관계 Metadata만 전달하는 모델을 검토한다.

## Frontend Split Decision

<small>PRD §100</small>

MVP:

```text
One Repository

FastAPI
+
Server-rendered UI
+
UI Lab
```

Phase 2 이후 다음 조건이 생기면 별도 Frontend를 검토한다.

```text
Authentication

Complex Watchlist Editing

Interactive Dependency Graph

Team Collaboration

Large Client-side State

Advanced Dashboard Interaction
```

기술 선택은 필요해질 때 결정한다.
