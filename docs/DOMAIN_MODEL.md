# 도메인 모델 — Health · Check · Detection · Change · Incident

> 이 문서는 KPubData Watch MVP PRD(v1.0 Draft, 2026-09-30)의 §6, §7, §8, §9, §10, §21, §22, §23, §24, §25, §26 를 목적별로 나눈 것이다. 전체 대응표는 [문서 안내](index.md#prd) 에 있다.

## Core Product Model

<small>PRD §6</small>

KPubData Watch의 가장 중요한 개념은:

```text
Health는 하나
Checks는 여러 개
```

이다.

잘못된 모델:

```text
Availability Health
Freshness Health
Schema Health
Volume Health
Null Health
Latency Health
...
```

Check 종류가 늘어날수록 UI와 도메인이 무한히 복잡해진다.

따라서 다음 구조를 사용한다.

```text
Dataset
│
├── Health
│
│   ├── Healthy
│   ├── Degraded
│   ├── Critical
│   └── Unknown
│
├── Checks
│
│   ├── Availability
│   ├── Freshness
│   ├── Contract
│   └── Quality
│       ├── Volume
│       └── Completeness
│
├── Changes
│
├── Incidents
│
└── Metrics
```

## Health Model

<small>PRD §7</small>

### 7.1 Dataset Health

Public UI에서는 Dataset마다 하나의 Health만 제공한다.

```text
HEALTHY
DEGRADED
CRITICAL
UNKNOWN
```

#### HEALTHY

현재 활성화된 Warning/Critical Incident가 없다.

#### DEGRADED

Dataset은 사용할 수 있지만 주의가 필요한 상태다.

예:

```text
Freshness delayed
Moderate volume anomaly
Non-fatal contract problem
```

#### CRITICAL

사용 불가능하거나 높은 장애 가능성이 있는 상태다.

예:

```text
Confirmed provider outage
Breaking contract change
Severe data anomaly
```

#### UNKNOWN

정상/비정상을 판단할 수 없다.

예:

```text
Watch scheduler failure
Monitoring credential failure
No valid observation yet
Internal probe error
```

매우 중요한 원칙:

```text
Watch 자체 장애
≠
Provider 장애
```

Watch가 확인하지 못했다고 Dataset을 장애로 표시하지 않는다.

## Check Result Model

<small>PRD §8</small>

개별 Check는 다음 상태를 반환한다.

```text
PASS
WARN
FAIL
UNKNOWN
NOT_APPLICABLE
```

`NOT_APPLICABLE`은 중요하다.

모든 Dataset에 모든 Check를 강제로 적용하지 않는다.

예:

```text
월간 정적 통계 Dataset

Availability   PASS
Freshness      PASS
Contract       PASS
Quality        PASS


갱신 시점을 판단할 방법이 없는 Dataset

Availability   PASS
Freshness      NOT_APPLICABLE
Contract       PASS
Quality        PASS
```

Freshness 는 Registry 의 필드 하나(`field: modified_at`)가 아니라 추출 종류(`kind`)로
선언되고, 레코드에서 갱신 시점을 뽑을 수 없는 Dataset 은 `freshness.enabled: false`
와 사유(`reason`)를 선언해 `NOT_APPLICABLE` 이 된다 — 예: 시간 필드가 설립일뿐인
`datago.hospital_info` ([Registry — Freshness 설정](REGISTRY.md#freshness)).

## Health Aggregation

<small>PRD §9</small>

Health는 Check 이름 자체가 아니라 **활성 Detection/Incident Severity**를 기준으로 결정한다.

기본 규칙:

```text
Active CRITICAL incident
        ↓
CRITICAL

Active WARNING incident
        ↓
DEGRADED

No active warning/critical
        ↓
HEALTHY

No reliable observation available
        ↓
UNKNOWN
```

INFO 수준의 Change는 Health를 낮추지 않는다.

예:

```text
Field added

Health
HEALTHY

Change
INFO — Contract changed
```

반면:

```text
Required field removed

Health
CRITICAL

Incident
Breaking contract change
```

## Health와 Change의 분리

<small>PRD §10</small>

KPubData Watch에서는 반드시 다음을 구분한다.

```text
Change
≠
Problem
```

예:

```text
+ new_field
```

이면:

```text
Health
Healthy

Change
Contract Changed
Severity: Info
```

반면:

```text
- required_field
```

이면:

```text
Health
Critical

Incident
Breaking Contract Change
```

따라서 내부 흐름은 다음과 같다.

```text
Observation
     ↓
Detection
     ↓
Change
     ↓
Incident
  (필요 시)
```

## Detection

<small>PRD §21</small>

Observation과 Detection은 분리한다.

```text
Observation
     ↓
Detection
```

Detection 예:

```json
{
  "dataset_id": "visitkorea-tourism",
  "observation_id": "...",

  "check": "contract",

  "result": "FAIL",
  "severity": "CRITICAL",

  "type": "field_removed",

  "evidence": {
    "field": "addr2",
    "previous_type": "string"
  }
}
```

## Evidence Schema

<small>PRD §22</small>

모든 중요한 Detection에는 다음 형태의 Evidence를 저장할 수 있어야 한다.

```json
{
  "expected": {},
  "observed": {},
  "difference": {},
  "rule": {},
  "first_seen_at": "...",
  "confirmed_at": "..."
}
```

UI는 이 Evidence를 사용해:

```text
Why was this detected?
```

를 설명한다.

## Change

<small>PRD §23</small>

Change는 관측된 사실이다.

예:

```text
Field added
Field removed
Type changed
Latest update changed
Provider response changed
```

Change는 반드시 장애라는 뜻이 아니다.

필드:

```text
id

dataset_id
observation_id

change_type
severity

title
summary

evidence

detected_at
created_at
```

Change는 원칙적으로 Immutable Event로 취급한다.

## Incident

<small>PRD §24</small>

Incident는 사용자가 대응해야 할 가능성이 높은 문제다.

예:

```text
API unavailable
Freshness delayed
Breaking contract change
Severe volume anomaly
Severe completeness anomaly
```

필드:

```text
id

dataset_id

incident_type

severity
status

started_at
detected_at
confirmed_at
resolved_at

title
summary

evidence

related_change_id

review_result
```

Incident 는 단일 `official_notice_url` 필드를 갖지 않는다 — Notice 는 독립
엔티티이고 N:N 링크로 연결된다(ADR 0011).

## Notice

<small>PRD §55 · ADR 0011 (#35)</small>

공식 공지(점검, 장애, 정정 등)는 독립 엔티티다. 등록·링크는 운영자 CLI 로
한다(자동 수집 없음, D-018).

필드:

```text
id

url
title
published_at
provider

excerpt
captured_at
registered_by
```

Incident 와 Change 에 N:N 으로 링크한다. 링크 레코드:

```text
notice_id
target_type
target_id

linked_at
linked_by
note
```

링크는 정보성이다 — 공지가 Incident 를 설명해도 자동 resolve 하지 않는다.
해소는 Watch 의 관측 근거(ADR 0009)만으로 한다.

## Incident Lifecycle

<small>PRD §25</small>

```text
OPEN
  ↓
ONGOING
  ↓
RESOLVED
```

운영자 판단:

```text
FALSE_POSITIVE
```

도 지원한다.

Detection 품질 개선을 위해 Incident에 다음 review를 저장한다.

```text
TRUE_POSITIVE
FALSE_POSITIVE
UNKNOWN
```

## Incident Severity

<small>PRD §26</small>

MVP에서는 세 단계만 사용한다.

```text
INFO
WARNING
CRITICAL
```

예:

| Event | Severity |
|---|---|
| Optional field added | INFO |
| Moderate freshness delay | WARNING |
| Moderate volume anomaly | WARNING |
| Required field removed | CRITICAL |
| Confirmed API outage | CRITICAL |

Dataset-specific override를 허용한다.
