# ADR 0001: MVP 는 Public Status 이고, 정본은 사업계획서와 최종 발표자료다

## 상태

채택됨(Accepted) — 2026-09-30 (PRD v1.0 Draft 결정 로그 D-001 · D-002 · D-003 · D-004 · D-018)

## 요약 (English summary)

> The MVP (0–3 months) is **Public Status**: observe, detect, keep history and
> publish status for 10 real public datasets. The business plan and the final
> presentation are the source of truth; the Business Model Canvas is not a design
> input. My Watchlist, dependency and impact come after the MVP, and official
> notices are linked by hand rather than crawled.

## 문제

제품 전체 비전은 `WATCH → DETECT → IMPACT` 이다. 이를 한 번에 SaaS 로 만들면 3개월 안에
검증 가능한 결과가 나오지 않는다. 또 설계 근거가 되는 자료가 여러 개(사업계획서, 발표자료,
Business Model Canvas)라서 무엇을 기준으로 범위를 정할지 먼저 정해야 한다.

## 결정

- **D-001** Canvas 는 MVP 설계 기준에서 제외한다.
- **D-002** 사업계획서와 최종 발표자료를 Source of Truth 로 사용한다.
- **D-003** MVP 는 Public Status 다: `WATCH → DETECT → HISTORY → PUBLIC STATUS`.
- **D-004** My Watchlist / Impact 는 MVP 이후다 (Phase 2 · Phase 3).
- **D-018** Official Notice 자동 Crawling 은 MVP P0 가 아니다. 초기에는 운영자가 공지 URL 을
  수동으로 연결한다.

기능 추가가 애매할 때의 판단 기준은 PRD 의 제품 경계다: *"이 기능이 없으면 Public Status 가
실제 공공데이터의 이상을 발견하고, 그 판단 근거를 설명할 수 없는가?"* — YES 면 MVP 고려,
NO 면 Backlog.

## 결과

- MVP 범위(P0/P1/유예)와 완료 조건은 [ROADMAP](../ROADMAP.md) 에 있다.
- 비목표(로그인, Watchlist, BYOK, 알림 채널, AI Explain, ML 등)는 제품 비전에서 제거하는 것이
  아니라 후속 단계로 미룬다 ([PRD](../PRD.md) MVP Non-Goals).
