# Detectors

> 이 문서는 KPubData Watch MVP PRD(v1.0 Draft, 2026-09-30)의 §11, §12, §27 를 목적별로 나눈 것이다. 전체 대응표는 [문서 안내](../index.md#prd) 에 있다.

Core Check 는 네 가지다. 각 Check 의 상세는 별도 문서에 있다.

| Check | 문서 | 질문 |
|---|---|---|
| Availability | [availability.md](availability.md) | API에 정상적으로 접근할 수 있는가? |
| Freshness | [freshness.md](freshness.md) | 데이터가 예정된 시점에 갱신되고 있는가? |
| Contract | [contract.md](contract.md) | 응답 구조·필드·타입이 바뀌었는가? |
| Quality (Volume · Completeness) | [quality.md](quality.md) | 데이터 양과 중요 Field 값이 평소와 크게 다른가? |

Check 결과 모델과 Health 집계는 [도메인 모델](../DOMAIN_MODEL.md) 에 있다.

## Metrics vs Health

<small>PRD §12</small>

모든 Metric을 Health Check로 만들지 않는다.

예:

```text
Latency
Response Size
Probe Duration
```

은 기본적으로 Metric이다.

```text
Metrics
├── latency_ms
├── response_size_bytes
└── probe_duration_ms
```

예:

```text
Latency

800ms
→
4.2s
```

만으로 데이터가 신뢰 불가능하다고 판단하지 않는다.

Timeout 수준이 되면 Availability에 영향을 준다.

## Confirmation / Flapping Protection

<small>PRD §27 · ADR 0009 (#31)</small>

한 번의 실패로 즉시 장애를 선언하지 않는 것을 기본값으로 한다. 전역 기본은
`2 failures → OPEN`, `2 successes → RESOLVE` 이고, Registry 는 `failures` 만
1~3 범위에서 사유를 적어 조정할 수 있다(`successes` 는 고정 — 플래핑 방지는
Dataset 사정이 아니다). Availability 는 즉시 재시도로 확인하므로 지연이
interval 과 무관하고, Freshness·Quality 는 다음 정기 probe 에서만 확인되므로
interval 에 비례한다(24시간↑ 주기는 `failures: 1` 권장). Contract(Breaking)
확인은 1회(ADR 0008).

**이 `failures` 카운터는 Watch 자체 실패를 세지 않는다.** D-009(ADR 0002)가
정한 대로, probe 가 provider 를 실제로 검사해 실패를 관측한 경우만 세고,
Watch 쪽 장애(네트워크 오류, 버그, 타임아웃 설정 오류 등으로 probe 자체를
실행하지 못한 경우)는 `UNKNOWN` 으로 남아 `failures` 에 들어가지 않는다.

### Availability

```text
Failure
  ↓
Confirmation Probe
  ↓
Failure
  ↓
Incident Open
```

기본:

```text
2 failures → OPEN
2 successes → RESOLVE
```

<small>[ADR 0009](../decisions/0009-confirmation-counts-global-default.md) (#31) —
전역 기본을 유지하되, Registry 가 `failures` 만 1~3 에서 사유와 함께 조정할 수
있다(`successes` 는 고정). Availability 의 확인 probe 는 즉시 재시도라 interval 과
무관하고, Freshness·Quality 는 다음 정기 probe 에서만 확인되므로 24시간 이상
주기의 Dataset 은 `failures: 1` 을 권장한다. Contract(Breaking) 확인은 1회
(ADR 0008).</small>

---

### Freshness

```text
Expected update window
        ↓
Grace period exceeded
        ↓
Confirmation probe
        ↓
Incident
```

---

### Contract

Breaking change:

```text
First detection
     ↓
Confirmation Probe
     ↓
Confirmed
     ↓
Incident
```
