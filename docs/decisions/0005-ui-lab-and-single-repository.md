# ADR 0005: UI 는 확정하지 않고 UI Lab 에서 실험한다 — 한 저장소, 최소 Server-rendered UI

## 상태

채택됨(Accepted) — 2026-09-30 (PRD v1.0 Draft 결정 로그 D-012 · D-013 · D-014 · D-015 · D-020)

## 요약 (English summary)

> The domain model and the read model are fixed; the UI layout is not. Three
> layouts (status page, provider-grouped, issues-first) are compared in a
> disposable UI Lab on 10, 50 and 150 dataset fixtures, all consuming the same read
> model. Frontend and backend stay in one repository, and Public Status ships a
> minimal server-rendered UI. The read API is designed so that provider, category,
> health and check filters can be added.

## 문제

Dataset 이 10개일 때 좋은 화면이 150개에서도 좋다는 보장이 없다. UI 를 먼저 확정하면 백엔드
도메인이 화면 배치에 묶이고, 반대로 백엔드를 먼저 만들면 UI 에 필요한 데이터 구조를 임의로
정하게 된다.

## 결정

- **D-012** UI 는 확정하지 않고 UI Lab 에서 실험한다. UI Lab 은 언제든 버릴 수 있고, Watch
  Engine 은 UI Lab 에 의존하지 않는다.
- **D-013** 10 / 50 / 150 Dataset Fixture 로 UI 확장성을 검증한다.
- **D-014** Frontend 와 Backend 를 별도 Repository 로 나누지 않는다. 별도 Frontend 는 Phase 2
  이후 인증·복잡한 Watchlist 편집 등이 생길 때 검토한다.
- **D-015** Public Status 에는 최소 Server-rendered UI 를 제공한다 (FastAPI + Jinja2).
- **D-020** Provider / Category / Health / Check 기준 Filter 확장을 고려한다 — Read API 부터 지원
  가능하게 설계한다.

연결점은 `Domain → Stable Read Model → Experimental UI` 이다. UI 가 DB Table 을 직접 해석하지
않는다.

## 결과

- 화면 원칙과 평가 기준은 [UI](../UI.md), Read API 는 [API 계약](https://github.com/kpubdata-lab/kpubdata-watch/blob/main/API_CONTRACT.md).
- 50~150 Dataset 에서 어떤 배치가 가장 효과적인지는 열린 질문이다 (#33).
