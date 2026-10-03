# 결정 기록 (ADR)

KPubData Watch 의 설계 결정. 형식은 KPubData 시리즈의 ADR 과 같다 — 한국어 본문에 영어 요약.

## ADR

| ADR | 결정 |
|---|---|
| [0001](0001-mvp-scope-public-status.md) | MVP 는 Public Status 이고, 정본은 사업계획서와 최종 발표자료다 |
| [0002](0002-one-health-many-checks.md) | Health 는 Dataset 당 하나, Check 는 여럿 — Change 와 Incident 는 분리한다 |
| [0003](0003-explainable-rule-based-detection.md) | MVP Detection 은 설명 가능한 Rule / Baseline 기반이다 — ML 은 쓰지 않는다 |
| [0004](0004-depend-on-kpubdata-only.md) | KPubData Watch 는 KPubData 에만 의존하고 Builder 에는 의존하지 않는다 |
| [0005](0005-ui-lab-and-single-repository.md) | UI 는 확정하지 않고 UI Lab 에서 실험한다 — 한 저장소, 최소 Server-rendered UI |
| [0006](0006-raw-response-storage.md) | 전체 Raw API Response 는 기본적으로 장기 저장하지 않는다 |
| [0007](0007-registry-declares-provider-rate-limits-and-terms.md) | Provider 의 Rate Limit 과 이용조건은 Registry 에 선언하고 검증이 지킨다 (#27) |
| [0008](0008-breaking-contract-default-severity.md) | Breaking Contract 변경의 기본 Severity 는 CRITICAL 이다 — 확인 후 개시, WARNING 까지만 하향 (#30) |
| [0009](0009-confirmation-counts-global-default.md) | 확인 횟수는 전역 기본(2 실패 개시·2 성공 해소)을 두고 Registry 가 failures 만 1~3 조정 (#31) |
| [0010](0010-public-history-default-period.md) | 공개 History 기본 기간은 30일, 조회 상한은 90일이다 (#32) |
| [0011](0011-notice-entity-manual-linking.md) | 공지는 독립 엔티티이고 Incident·Change 에 N:N 수동 링크된다 (#35) |
| [0012](0012-pages-hosts-a-fixture-demo-not-the-service.md) | GitHub Pages 는 고정 Fixture 기반 Public Status 데모와 문서만 호스팅한다 — 운영 서비스는 FastAPI + Worker + PostgreSQL 그대로다 (#78) |
| [0013](0013-overview-now-and-history-views.md) | Overview 는 현재 스냅샷, History 는 최근 30일로 나눈다 — 허용 시각화는 상태 이력과 Evidence 두 가지뿐이다 (#108) |

## PRD 결정 로그 대응표

<small>PRD §104 Decision Log</small>

PRD v1.0 Draft 가 확정한 결정 D-001~D-020 이 어느 ADR 에 기록됐는지.

| 결정 | 내용 | ADR |
|---|---|---|
| D-001 | Canvas는 MVP 설계 기준에서 제외한다. | [ADR 0001](0001-mvp-scope-public-status.md) |
| D-002 | 사업계획서와 최종 발표자료를 Source of Truth로 사용한다. | [ADR 0001](0001-mvp-scope-public-status.md) |
| D-003 | MVP는 Public Status다. | [ADR 0001](0001-mvp-scope-public-status.md) |
| D-004 | My Watchlist / Impact는 MVP 이후다. | [ADR 0001](0001-mvp-scope-public-status.md) |
| D-005 | Health는 Dataset당 하나다. | [ADR 0002](0002-one-health-many-checks.md) |
| D-006 | Availability / Freshness / Contract / Quality는 Checks다. | [ADR 0002](0002-one-health-many-checks.md) |
| D-007 | Change와 Incident를 분리한다. | [ADR 0002](0002-one-health-many-checks.md) |
| D-008 | 정보성 Change는 Health를 낮추지 않는다. | [ADR 0002](0002-one-health-many-checks.md) |
| D-009 | Watch 자체 실패를 Dataset 장애로 표시하지 않는다. | [ADR 0002](0002-one-health-many-checks.md) |
| D-010 | MVP Detection은 설명 가능한 Rule/Baseline 기반이다. | [ADR 0003](0003-explainable-rule-based-detection.md) |
| D-011 | ML / Seasonality Learning은 MVP에서 제외한다. | [ADR 0003](0003-explainable-rule-based-detection.md) |
| D-012 | UI는 확정하지 않고 UI Lab에서 실험한다. | [ADR 0005](0005-ui-lab-and-single-repository.md) |
| D-013 | 10 / 50 / 150 Dataset Fixture로 UI 확장성을 검증한다. | [ADR 0005](0005-ui-lab-and-single-repository.md) |
| D-014 | Frontend와 Backend를 별도 Repository로 나누지 않는다. | [ADR 0005](0005-ui-lab-and-single-repository.md) |
| D-015 | Public Status에는 최소 Server-rendered UI를 제공한다. | [ADR 0005](0005-ui-lab-and-single-repository.md) |
| D-016 | KPubData Watch는 KPubData에 의존할 수 있지만 Builder에는 의존하지 않는다. | [ADR 0004](0004-depend-on-kpubdata-only.md) |
| D-017 | 전체 Raw API Response를 기본적으로 장기 저장하지 않는다. | [ADR 0006](0006-raw-response-storage.md) |
| D-018 | Official Notice 자동 Crawling은 MVP P0가 아니다. | [ADR 0001](0001-mvp-scope-public-status.md) |
| D-019 | Latency는 기본적으로 Metric이며 Health Dimension이 아니다. | [ADR 0002](0002-one-health-many-checks.md) |
| D-020 | Provider / Category / Health / Check 기준 Filter 확장을 고려한다. | [ADR 0005](0005-ui-lab-and-single-repository.md) |

## 새 결정을 추가할 때

- 번호는 다음 빈 번호를 쓴다. 파일 이름은 `NNNN-짧은-설명.md`.
- 상태(`제안됨`/`채택됨`/`대체됨`), English summary, 문제, 결정, 결과를 적는다.
- 이 디렉터리는 CODEOWNERS 대상이다.
- 열린 질문(PRD §105)은 이슈로 관리하고, 답이 결정이면 여기에 ADR 로 남긴다 ([로드맵](../ROADMAP.md#open-questions)).
