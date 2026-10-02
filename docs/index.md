# KPubData Watch 문서

한국 공공데이터 API 를 지속적으로 관측하고, **"이 공공데이터를 지금 믿고 사용할 수 있는가?"** 를
근거와 함께 답하는 Public Data Reliability 서비스입니다.

## 어디서부터 읽나

| 문서 | 내용 |
|---|---|
| [PRD](PRD.md) | 제품 정의 · 문제 · 원칙 · 목표 · 비목표 · 성공 지표 |
| [로드맵](ROADMAP.md) | MVP 범위(P0/P1/유예) · 구현 순서 · 완료 조건 · Epic · 열린 질문 · 이후 단계 |
| [도메인 모델](DOMAIN_MODEL.md) | Health · Check · Detection · Change · Incident |
| [Detectors](detectors/README.md) | Availability · Freshness · Contract · Quality |
| [아키텍처](architecture/README.md) | Probe · Observation · Scheduler · 저장 · 관측성 · 배포 |
| [Registry](REGISTRY.md) | Dataset Registry 형식과 Dataset 선정 기준 |
| [UI](UI.md) | UI 전략 · UI Lab · Public Status 화면 원칙 |
| [시각 정체성](VISUAL_IDENTITY.md) | KPubData Studio Brand v2 — 로고 · 토큰 · 상태색 · 접근성 (고정) |
| [테스트](TESTING.md) | 테스트 전략과 CI 게이트 |
| [결정 기록](decisions/README.md) | ADR 과 PRD 결정 로그 대응표 |
| [API 계약](https://github.com/yeongseon/kpubdata-watch/blob/main/API_CONTRACT.md) | Public Read API 와 운영자 CLI (초안, English) |
| [SECURITY](https://github.com/yeongseon/kpubdata-watch/blob/main/SECURITY.md) | 보안 신고와 credential · redaction 요구사항 (English) |

## PRD

원래의 PRD(`prd.md`, v1.0 Draft, 2026-09-30)는 한 파일에 제품·설계·계약·일정이 모두 들어 있었다.
목적에 맞게 나눈 뒤 각 절이 어디로 갔는지가 아래 표다. 각 문서의 절 제목 아래 `PRD §N` 표시가
원문 위치를 가리킨다. Development Epic(§81–§93)과 Open Questions(§105)는 GitHub 이슈로도
관리한다.

| PRD 절 | 제목 | 문서 |
|---|---|---|
| §0 | Executive Summary | [PRD](PRD.md) |
| §1 | Product Vision | [PRD](PRD.md) |
| §2 | Problem | [PRD](PRD.md) |
| §3 | Product Principle | [PRD](PRD.md) |
| §4 | MVP Goals | [PRD](PRD.md) |
| §5 | MVP Non-Goals | [PRD](PRD.md) |
| §6 | Core Product Model | [도메인 모델](DOMAIN_MODEL.md) |
| §7 | Health Model | [도메인 모델](DOMAIN_MODEL.md) |
| §8 | Check Result Model | [도메인 모델](DOMAIN_MODEL.md) |
| §9 | Health Aggregation | [도메인 모델](DOMAIN_MODEL.md) |
| §10 | Health와 Change의 분리 | [도메인 모델](DOMAIN_MODEL.md) |
| §11 | Core Checks | [Detectors](detectors/README.md) |
| §11.1 | Availability | [Availability](detectors/availability.md) |
| §11.2 | Freshness | [Freshness](detectors/freshness.md) |
| §11.3 | Contract | [Contract](detectors/contract.md) |
| §11.4 | Contract Change Classification | [Contract](detectors/contract.md) |
| §11.5 | Quality | [Quality](detectors/quality.md) |
| §11.6 | Volume | [Quality](detectors/quality.md) |
| §11.7 | Completeness | [Quality](detectors/quality.md) |
| §12 | Metrics vs Health | [Detectors](detectors/README.md) |
| §13 | Dataset Registry | [Registry](REGISTRY.md) |
| §14 | Provider / Dataset / Probe Model | [아키텍처](architecture/README.md) |
| §15 | Probe Principle | [아키텍처](architecture/README.md) |
| §16 | Probe Pipeline | [아키텍처](architecture/README.md) |
| §17 | Probe Result | [아키텍처](architecture/README.md) |
| §18 | Observation | [아키텍처](architecture/README.md) |
| §19 | Raw Data Storage Policy | [아키텍처](architecture/README.md) |
| §20 | Schema Snapshot | [아키텍처](architecture/README.md) |
| §21 | Detection | [도메인 모델](DOMAIN_MODEL.md) |
| §22 | Evidence Schema | [도메인 모델](DOMAIN_MODEL.md) |
| §23 | Change | [도메인 모델](DOMAIN_MODEL.md) |
| §24 | Incident | [도메인 모델](DOMAIN_MODEL.md) |
| §25 | Incident Lifecycle | [도메인 모델](DOMAIN_MODEL.md) |
| §26 | Incident Severity | [도메인 모델](DOMAIN_MODEL.md) |
| §27 | Confirmation / Flapping Protection | [Detectors](detectors/README.md) |
| §28 | Scheduling | [아키텍처](architecture/README.md) |
| §29 | Scheduler Architecture | [아키텍처](architecture/README.md) |
| §30 | Overall Architecture | [아키텍처](architecture/README.md) |
| §31 | Repository Structure | [아키텍처](architecture/README.md) |
| §32 | Technology Recommendation | [아키텍처](architecture/README.md) |
| §33 | UI Strategy | [UI](UI.md) |
| §34 | UI Architecture | [UI](UI.md) |
| §35 | UI Read Model | [UI](UI.md) |
| §36 | UI Lab | [UI](UI.md) |
| §37 | UI Lab Fixtures | [UI](UI.md) |
| §38 | UI Experiment A — Status Page | [UI](UI.md) |
| §39 | UI Experiment B — Provider Group | [UI](UI.md) |
| §40 | UI Experiment C — Issue First | [UI](UI.md) |
| §41 | UI Evaluation Criteria | [UI](UI.md) |
| §42 | Public Status Information Architecture | [UI](UI.md) |
| §43 | Public Status Page | [UI](UI.md) |
| §44 | Search / Filtering | [UI](UI.md) |
| §45 | Provider Grouping | [UI](UI.md) |
| §46 | Dataset List Density | [UI](UI.md) |
| §47 | Dataset Detail | [UI](UI.md) |
| §48 | Why Was This Detected? | [UI](UI.md) |
| §49 | Contract Diff UX | [UI](UI.md) |
| §50 | History UX | [UI](UI.md) |
| §51 | Charts | [UI](UI.md) |
| §52 | Visual Design Principles | [UI](UI.md) |
| §53 | Color Semantics | [UI](UI.md) |
| §54 | Time UX | [UI](UI.md) |
| §55 | Official Notice | [UI](UI.md) |
| §56 | Public Read API | [API 계약](https://github.com/yeongseon/kpubdata-watch/blob/main/API_CONTRACT.md) (English) |
| §57 | GET `/api/v1/datasets` | [API 계약](https://github.com/yeongseon/kpubdata-watch/blob/main/API_CONTRACT.md) (English) |
| §58 | GET `/api/v1/datasets/{id}` | [API 계약](https://github.com/yeongseon/kpubdata-watch/blob/main/API_CONTRACT.md) (English) |
| §59 | History API | [API 계약](https://github.com/yeongseon/kpubdata-watch/blob/main/API_CONTRACT.md) (English) |
| §60 | Operator Interface | [API 계약](https://github.com/yeongseon/kpubdata-watch/blob/main/API_CONTRACT.md) (English) |
| §61 | Credentials | [SECURITY](https://github.com/yeongseon/kpubdata-watch/blob/main/SECURITY.md) (English) |
| §62 | Secret Redaction | [SECURITY](https://github.com/yeongseon/kpubdata-watch/blob/main/SECURITY.md) (English) |
| §63 | Security Requirements | [SECURITY](https://github.com/yeongseon/kpubdata-watch/blob/main/SECURITY.md) (English) |
| §64 | Monitoring Reliability | [아키텍처](architecture/README.md) |
| §65 | Watch Internal Observability | [아키텍처](architecture/README.md) |
| §66 | Database Model | [아키텍처](architecture/README.md) |
| §67 | Retention | [아키텍처](architecture/README.md) |
| §68 | Dataset Selection | [Registry](REGISTRY.md) |
| §69 | Initial Dataset Portfolio | [Registry](REGISTRY.md) |
| §70 | Test Strategy | [테스트](TESTING.md) |
| §71 | Fixture Regression Tests | [테스트](TESTING.md) |
| §72 | Replay Tests | [테스트](TESTING.md) |
| §73 | Integration Tests | [테스트](TESTING.md) |
| §74 | Live Tests | [테스트](TESTING.md) |
| §75 | CI Quality Gates | [테스트](TESTING.md) |
| §76 | Non-Functional Requirements | [아키텍처](architecture/README.md) · [API 계약](https://github.com/yeongseon/kpubdata-watch/blob/main/API_CONTRACT.md) |
| §77 | Deployment | [아키텍처](architecture/README.md) |
| §78 | MVP Functional Scope | [로드맵](ROADMAP.md) |
| §79 | P1 — 시간이 허용하면 | [로드맵](ROADMAP.md) |
| §80 | Explicitly Deferred | [로드맵](ROADMAP.md) |
| §81 | Development Epics | [로드맵](ROADMAP.md) |
| §82 | Epic 2 — Dataset Registry | [로드맵](ROADMAP.md) |
| §83 | Epic 3 — Probe Runtime | [로드맵](ROADMAP.md) |
| §84 | Epic 4 — Observation | [로드맵](ROADMAP.md) |
| §85 | Epic 5 — Availability | [로드맵](ROADMAP.md) |
| §86 | Epic 6 — Contract | [로드맵](ROADMAP.md) |
| §87 | Epic 7 — Freshness | [로드맵](ROADMAP.md) |
| §88 | Epic 8 — Quality | [로드맵](ROADMAP.md) |
| §89 | Epic 9 — Incident & Health | [로드맵](ROADMAP.md) |
| §90 | Epic 10 — Read API | [로드맵](ROADMAP.md) |
| §91 | Epic 11 — Public Status UI | [로드맵](ROADMAP.md) |
| §92 | Epic 12 — UI Lab | [로드맵](ROADMAP.md) |
| §93 | Epic 13 — Production Hardening | [로드맵](ROADMAP.md) |
| §94 | Definition of Done — MVP | [로드맵](ROADMAP.md) |
| §95 | MVP Success Metrics | [PRD](PRD.md) |
| §96 | UI Success Metrics | [PRD](PRD.md) |
| §97 | Roadmap After MVP | [로드맵](ROADMAP.md) |
| §98 | Phase 3 — Impact | [로드맵](ROADMAP.md) |
| §99 | Usage Manifest — Future | [로드맵](ROADMAP.md) |
| §100 | Frontend Split Decision | [로드맵](ROADMAP.md) |
| §101 | Key Product Boundary | [PRD](PRD.md) |
| §102 | Final MVP Shape | [PRD](PRD.md) |
| §103 | Product Statement | [PRD](PRD.md) |
| §104 | Decision Log | [결정 기록](decisions/README.md) |
| §105 | Open Questions | [로드맵 — Open Questions](ROADMAP.md#open-questions) · 이슈 |
| §106 | Recommended Implementation Order | [로드맵](ROADMAP.md) |
| §107 | Final Principle | [PRD](PRD.md) |
