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

<small>PRD §27</small>

한 번의 실패로 즉시 장애를 선언하지 않는 것을 기본값으로 한다.

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
