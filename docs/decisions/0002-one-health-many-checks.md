# ADR 0002: Health 는 Dataset 당 하나, Check 는 여럿 — Change 와 Incident 는 분리한다

## 상태

채택됨(Accepted) — 2026-09-30 (PRD v1.0 Draft 결정 로그 D-005 · D-006 · D-007 · D-008 · D-009 · D-019)

## 요약 (English summary)

> Each dataset has exactly one health (`HEALTHY`, `DEGRADED`, `CRITICAL`,
> `UNKNOWN`), derived from the severity of active detections and incidents.
> Availability, Freshness, Contract and Quality are checks, not healths. A change
> is an observed fact and does not lower health unless it becomes an incident.
> Watch's own failure makes a dataset `UNKNOWN`, never an outage. Latency is a
> metric, not a health dimension.

## 문제

Check 종류마다 Health 를 두면(Availability Health, Freshness Health, Schema Health, …)
Check 가 늘어날수록 UI 와 도메인이 무한히 복잡해진다. 또 "필드가 추가됐다" 같은 사실과
"사용자가 대응해야 할 문제" 를 구분하지 않으면 정상 Dataset 이 장애처럼 보이고, Watch 가
확인하지 못한 것을 Provider 장애로 공개하게 된다.

## 결정

- **D-005** Health 는 Dataset 당 하나다.
- **D-006** Availability / Freshness / Contract / Quality 는 Check 다.
- **D-007** Change 와 Incident 를 분리한다: `Observation → Detection → Change → Incident(필요 시)`.
- **D-008** 정보성(INFO) Change 는 Health 를 낮추지 않는다.
- **D-009** Watch 자체 실패를 Dataset 장애로 표시하지 않는다 — `UNKNOWN` 으로 둔다.
- **D-019** Latency 는 기본적으로 Metric 이며 Health Dimension 이 아니다. Timeout 수준이 되면
  Availability 에 영향을 준다.

Health 집계 규칙: 활성 CRITICAL incident → CRITICAL, 활성 WARNING incident → DEGRADED,
활성 warning/critical 없음 → HEALTHY, 신뢰할 관측 없음 → UNKNOWN.

## 결과

- 모델 전체는 [도메인 모델](../DOMAIN_MODEL.md), Check 별 판정은 [Detectors](../detectors/README.md).
- 새 신호를 추가할 때 새 Health 를 만들지 않는다. Check 이거나 Metric 이다.
- 기본 Severity 와 Confirmation 횟수의 세부값은 열린 질문이다 (#30, #31).
