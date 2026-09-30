# KPubData Watch — MVP 제품 요구사항 (PRD)

> Version: 1.0 Draft  
> Product: KPubData Watch  
> MVP: Public Status  
> Target: 0–3 months  
> Status: Ready for implementation planning  
> Source of Truth: KPubData Watch 사업계획서 + 최종 발표자료  
> Business Model Canvas: MVP 설계 기준에서 제외

> 이 문서는 KPubData Watch MVP PRD(v1.0 Draft, 2026-09-30)의 §0, §1, §2, §3, §4, §5, §95, §96, §101, §102, §103, §107 를 목적별로 나눈 것이다. 전체 대응표는 [문서 안내](index.md#prd) 에 있다.

설계 세부는 목적별 문서로 나뉘어 있다: [도메인 모델](DOMAIN_MODEL.md) · [Detectors](detectors/README.md) ·
[아키텍처](architecture/README.md) · [Registry](REGISTRY.md) · [UI](UI.md) · [테스트](TESTING.md) ·
[로드맵](ROADMAP.md) · [결정 기록](decisions/README.md) · [API 계약](https://github.com/yeongseon/kpubdata-watch/blob/main/API_CONTRACT.md) ·
[보안](https://github.com/yeongseon/kpubdata-watch/blob/main/SECURITY.md).

## Executive Summary

<small>PRD §0</small>

KPubData Watch는 한국 공공데이터 API를 지속적으로 관측하고,

> **"이 공공데이터를 지금 믿고 사용할 수 있는가?"**

를 판단하기 위한 Public Data Reliability 서비스다.

제품 전체 비전은 다음과 같다.

```text
WATCH
공공데이터를 지속 관측
    ↓
DETECT
변경·중단·데이터 이상 감지
    ↓
IMPACT
실제 사용 Dataset/Field와 연결하여
서비스 영향을 판단
```

다만 MVP에서는 전체 SaaS를 한 번에 구현하지 않는다.

```text
MVP — 0~3개월

WATCH
  ↓
DETECT
  ↓
HISTORY
  ↓
PUBLIC STATUS
```

이후 단계에서 다음을 추가한다.

```text
Phase 2

MY WATCHLIST
  ↓
DATASET / FIELD DEPENDENCY
  ↓
ALERT


Phase 3

DEPENDENCY
  ↓
IMPACT
  ↓
TEAM / ENTERPRISE
```

MVP의 핵심 목표는 다음과 같다.

> **10개의 실제 한국 공공데이터 Dataset을 지속 관측하고,  
> 현재 상태와 변경·이상 이력을 공개적으로 설명할 수 있는 시스템을 만든다.**

## Product Vision

<small>PRD §1</small>

KPubData가 해결하는 질문은 다음과 같다.

> "한국 공공데이터를 어떻게 일관된 방식으로 사용할 것인가?"

KPubData Watch는 그 다음 질문을 해결한다.

> **"오늘 정상적으로 사용한 데이터가 내일도 같은 구조와 상태일 것이라는 것을 어떻게 알 수 있는가?"**

제품 전체 관계는 다음과 같다.

```text
                   KPubData
              Public Data SDK
                    │
          ┌─────────┴─────────┐
          │                   │
       Builder               Watch
          │                   │
          ▼                   ▼
    Dataset Artifact      Observation
          │                   │
       Studio           Change / Incident
                              │
                           History
                              │
                         Public Status
```

의존성 원칙:

```text
kpubdata-watch
      ↓
   kpubdata
```

허용하지 않는 구조:

```text
kpubdata-watch
      ↓
kpubdata-builder
```

Builder와 Watch는 sibling product로 유지한다.

필요한 상호운용은 향후 Manifest / Artifact / Protocol로 처리한다.

## Problem

<small>PRD §2</small>

공공 API는 다음과 같은 변화를 겪을 수 있다.

```text
Endpoint 변경
Request parameter 변경
Field 추가/삭제
Field type 변경
Response structure 변경
Pagination 변경
API 중단
데이터 갱신 지연
데이터 건수 급감
결측률 증가
```

문제는 API 요청 자체는 성공할 수 있다는 것이다.

예:

```text
HTTP 200 OK

하지만

latest_data_at = 3일 전
```

또는:

```text
HTTP 200 OK

평소 records = 10,000 내외

현재 records = 6,300
```

또는:

```text
Before

{
  "addr1": "...",
  "addr2": "..."
}

After

{
  "addr1": "..."
}
```

따라서 다음 등식은 성립하지 않는다.

```text
HTTP 200
    ≠
Data Healthy
```

KPubData Watch는 HTTP uptime뿐 아니라 데이터 자체의 신뢰성까지 관찰한다.

## Product Principle

<small>PRD §3</small>

MVP의 모든 설계는 다음 네 가지 원칙을 따른다.

```text
Simple
Explainable
Reproducible
Evidence-based
```

특히 다음과 같은 결과는 허용하지 않는다.

```text
"AI가 이상하다고 판단했습니다."
```

대신 항상 판단 근거를 설명할 수 있어야 한다.

예:

```text
Freshness delayed

Expected
2026-09-30 06:00 KST ± 60 min

Observed
Latest data: 2026-09-29 06:04 KST

Detected
2026-09-30 07:11 KST

Rule
latest_data_at exceeded expected update window
```

모든 Detection은 최소한 다음을 설명할 수 있어야 한다.

```text
Expected
Observed
Difference
Rule
Evidence
Timestamp
```

## MVP Goals

<small>PRD §4</small>

### 4.1 Primary Goal

10개의 공공 Dataset을 실제로 지속 관측하고 아래 정보를 제공한다.

```text
Current Health
Last Checked
Last Successful Check
Availability
Freshness
Contract Changes
Quality Signals
Recent Changes
Incidents
History
```

---

### 4.2 Product Validation Goals

MVP 기간 동안 다음을 검증한다.

```text
Monitored datasets        ≥ 10
Providers                 ≥ 3

실제 변화/장애 사례       ≥ 10
활용기업 인터뷰           ≥ 10
베타 후보 기업            ≥ 3
```

기능 개발 자체보다 다음 가설 검증이 중요하다.

> 공공데이터를 사용하는 조직이  
> 변경·중단·갱신 이상을 별도로 관리해야 하는 실제 문제가 존재하는가?

## MVP Non-Goals

<small>PRD §5</small>

MVP에서는 다음 기능을 구현하지 않는다.

```text
User Login
User Account
Organization
Billing
Payment

My Watchlist
User BYOK

Team
Role / Permission

Usage Manifest
Automatic Dependency Discovery

Service Impact Analysis

Slack
Microsoft Teams
Webhook

AI Explain
AI Migration Code

ML anomaly detection
Automatic seasonal learning

B2G Dashboard

Multi-tenant SaaS Architecture

Separate React / Next.js frontend repository
```

이 기능들은 제품 비전에서 제거하는 것이 아니라 후속 단계로 미룬다.

## Key Product Boundary

<small>PRD §101</small>

개발 중 기능 추가 여부가 애매하면 다음 질문으로 판단한다.

> **"이 기능이 없으면 Public Status가 실제 공공데이터의 이상을 발견하고, 그 판단 근거를 설명할 수 없는가?"**

YES:

```text
MVP 고려
```

NO:

```text
Backlog
```

## MVP Success Metrics

<small>PRD §95</small>

### Engineering

```text
Datasets                   ≥ 10

Providers                  ≥ 3

Probe execution success    측정

Detection types            ≥ 4

History                    지속 축적

Critical secret leakage    0
```

---

### Detection Quality

운영자가 Incident를 평가한다.

```text
TRUE_POSITIVE

FALSE_POSITIVE

UNKNOWN
```

초기부터 임의로:

```text
95% accuracy
```

같은 목표는 두지 않는다.

실제 History가 축적된 후 KPI를 정한다.

---

### Product Validation

```text
Real change / incident cases ≥ 10

User interviews              ≥ 10

Beta candidates              ≥ 3
```

## UI Success Metrics

<small>PRD §96</small>

UI는 정량/정성적으로 다음을 평가한다.

```text
Time to identify active issue

Time to find affected Dataset

Time to understand detection reason

Search success

Provider navigation clarity

150 Dataset scanability

Mobile readability
```

## Final MVP Shape

<small>PRD §102</small>

```text
                   10 Public Datasets
                           │
                           ▼
                        Probe
                           │
                           ▼
                     Observation
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
 Availability          Freshness          Contract
                                               │
                                               ▼
                                            Quality
                                      ┌────────┴────────┐
                                      ▼                 ▼
                                    Volume        Completeness

        └──────────────────┬──────────────────┘
                           │
                           ▼
                       Detection
                           │
               ┌───────────┴───────────┐
               ▼                       ▼
             Change                  Incident
               │                       │
               └───────────┬───────────┘
                           ▼
                         Health
                           │
                           ▼
                         History
                           │
                           ▼
                       Read API
                           │
                  ┌────────┴────────┐
                  ▼                 ▼
            Public Status         UI Lab
```

## Product Statement

<small>PRD §103</small>

### Product

**KPubData Watch**

### MVP

**Public Data Health / Public Status**

### MVP Question

> **이 공공데이터를 지금 믿고 사용할 수 있는가?**

### Product Vision

> **무엇이 바뀌었는가를 넘어,  
> 그 변화가 내 서비스에 영향을 주는가까지 알려준다.**

## Final Principle

<small>PRD §107</small>

KPubData Watch MVP의 성공은:

> **예쁜 Dashboard를 만드는 것**

이 아니다.

성공 기준은:

> **실제 공공데이터를 장기간 관측하고,  
> 문제가 발생했을 때 무엇이 달라졌는지 탐지하며,  
> 왜 문제라고 판단했는지를 증거와 함께 설명할 수 있는 것**

이다.

UI는 이 신뢰성 데이터를 가장 잘 전달하는 방법을 실험한다.

따라서 MVP 개발의 우선순위는:

```text
Observation
    >
Detection
    >
Evidence
    >
History
    >
Health
    >
API
    >
UI Optimization
```

으로 둔다.
