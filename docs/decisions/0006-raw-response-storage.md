# ADR 0006: 전체 Raw API Response 는 기본적으로 장기 저장하지 않는다

## 상태

채택됨(Accepted) — 2026-09-30 (PRD v1.0 Draft 결정 로그 D-017)

## 요약 (English summary)

> Watch stores what a verdict needs — status, timing, counts, freshness timestamp,
> schema and its hash, a sample hash, quality metrics and detection evidence — and
> not full response bodies, the raw dataset, API keys, authorization headers or
> sensitive query parameters. A short-lived, opt-in, sanitised debug sample may be
> added later; the MVP does not need one.

## 문제

Probe 는 Dataset 전체를 복제하는 작업이 아니다. 매 관측의 전체 응답을 쌓으면 비용이 커지고,
원본 데이터 재배포와 credential·개인정보가 섞일 위험이 생긴다. 반대로 판정 근거는 오래
남아야 한다.

## 결정

- **D-017** 전체 Raw API Response 를 기본적으로 장기 저장하지 않는다.
- 저장: Status, Timing, Count, Freshness Timestamp, Schema, Schema Hash, Sample Hash,
  Quality Metrics, Detection Evidence.
- 저장하지 않음: 전체 Raw Dataset, 전체 Response Body, API Key, Authorization Header,
  Sensitive Query Parameters.
- 필요하면 향후 Debug Sample 을 Short TTL · Explicit Opt-in · Sanitized 방식으로 도입한다.
  MVP P0 에서는 필요하지 않다.
- Schema 는 매 Observation 마다 중복 저장하지 않고, 바뀔 때만 SchemaSnapshot 을 남긴다.

## 결과

- 보존 기간: Public history 최소 30일, Internal metadata 최소 90일. Schema Snapshot · Change ·
  Incident 는 가능한 한 장기 보관 ([아키텍처](../architecture/README.md) Retention). 공개 이력의
  기본 기간은 열린 질문이다 (#32).
- Replay test 의 before/after fixture 는 이 원칙의 예외가 아니다 — 비밀·민감 데이터를 지운
  최소 사례만 테스트 fixture 로 보존한다 (#43).
