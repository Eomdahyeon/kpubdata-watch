# ADR 0003: MVP Detection 은 설명 가능한 Rule / Baseline 기반이다 — ML 은 쓰지 않는다

## 상태

채택됨(Accepted) — 2026-09-30 (PRD v1.0 Draft 결정 로그 D-010 · D-011)

## 요약 (English summary)

> Every MVP detection is a rule or a baseline a person can check by hand, and
> records Expected, Observed, Difference, Rule, Evidence and Timestamp. Machine
> learning and learned seasonality are out of the MVP. "The AI decided this looks
> wrong" is never an acceptable result.

## 문제

Watch 의 가치는 "문제가 있다" 가 아니라 "왜 문제라고 판단했는가" 를 증거와 함께 설명하는
데 있다. ML 이상 탐지는 초기 관측 이력이 없는 상태에서 오탐을 설명할 수 없고, 판정 근거를
공개 화면에 보일 수 없다.

## 결정

- **D-010** MVP Detection 은 설명 가능한 Rule/Baseline 기반이다. Volume 은 Rolling median 과
  Dataset 별 threshold, Freshness 는 선언된 갱신 주기와 grace period, Contract 는 canonical
  schema diff 로 판정한다.
- **D-011** ML / Seasonality Learning 은 MVP 에서 제외한다.

모든 Detection 은 최소한 Expected · Observed · Difference · Rule · Evidence · Timestamp 를
설명할 수 있어야 한다. Baseline 이 충분하지 않으면 `UNKNOWN`(또는 "Baseline building") 이다.

## 결과

- Evidence 형식은 [도메인 모델](../DOMAIN_MODEL.md) 의 Evidence Schema.
- 정확도 KPI(예: 95%)는 처음부터 두지 않고, 운영자 review(TRUE_POSITIVE / FALSE_POSITIVE /
  UNKNOWN)가 쌓인 뒤 정한다 ([PRD](../PRD.md) MVP Success Metrics).
