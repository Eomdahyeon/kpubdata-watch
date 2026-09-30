# Freshness

> 이 문서는 KPubData Watch MVP PRD(v1.0 Draft, 2026-09-30)의 §11.2 를 목적별로 나눈 것이다. 전체 대응표는 [문서 안내](../index.md#prd) 에 있다.

## Freshness

<small>PRD §11.2</small>

질문:

> 데이터가 예정된 시점에 갱신되고 있는가?

Dataset Registry에 명시적으로 설정한다.

예:

```yaml
freshness:
  enabled: true
  field: modified_at

  timezone: Asia/Seoul

  expected_interval: 24h
  grace_period: 2h
```

예:

```text
Expected
Daily update

Latest data
2026-09-30 05:58 KST

Current time
2026-09-30 07:10 KST

Result
PASS
```

또는:

```text
Expected
06:00 ± 1h

Latest data
Previous day 06:04

Result
WARN

Freshness delayed
```

Freshness는 공공데이터 특화 기능 중 핵심으로 취급한다.
