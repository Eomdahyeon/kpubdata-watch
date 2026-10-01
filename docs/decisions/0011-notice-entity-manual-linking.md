# ADR 0011: 공지는 독립 엔티티이고 Incident·Change 에 N:N 수동 링크된다

## 상태

채택됨(Accepted) — 2026-10-01 (#35, PRD §105 Q-011)

## 요약 (English summary)

> An official notice is its own entity — url, title, published time, provider,
> a short excerpt captured at registration, who registered it — and operators
> link it to incidents and changes many-to-many from the CLI. A single
> `official_notice_url` field on the incident (the PRD sketch) cannot express
> one maintenance notice covering several datasets, or a correction notice
> joining an incident that already has one. Linking is informational: a notice
> explains an observation but never resolves an incident — resolution stays
> evidence-driven. The observed-vs-published time pair the UI shows becomes a
> trust signal about the provider.

## 문제

PRD §55 는 "Operator manually attaches official notice URL" 로 수동 등록을 정하고
(D-018: 자동 Crawling 은 P0 아님), Incident 모델에 `official_notice_url` 필드가
있다. 그러나:

- 하나의 점검 공지가 여러 Dataset·서비스에 걸친다 — Dataset 마다 같은 URL 를
  복사해 붙이면 공지의 정체성이 없어진다.
- 하나의 Incident 에 사후 정정 공지가 추가로 붙을 수 있다 — 단일 필드는 안 된다.
- 공지 페이지는 바뀌거나 사라진다 — URL 만 저장하면 근거가 소실된다.
- Change 는 공지가 유일한 설명인 경우가 많다(정보성 변경) — 링크 대상이
  Incident 만이어서는 안 된다.

## 결정

1. **Notice 는 독립 엔티티다.** 필드: `url`(정본), `title`, `published_at`,
   `provider`(선택), `excerpt`(선택 — 등록 시점 발췌, 근거 보존), `captured_at`,
   `registered_by`. 등록·링크는 운영자 CLI 로 한다(자동 수집 없음, D-018).
2. **링크는 N:N, 대상은 Incident 와 Change.** 링크 레코드는
   `(notice, target_type, target_id)` 와 `linked_at`, `linked_by`, `note`(선택)를
   남긴다. Incident 의 `official_notice_url` 필드는 이 관계로 대체한다.
3. **링크는 정보성이다.** 공지가 Incident 를 설명해도 자동 resolve 하지 않는다 —
   해소는 Watch 의 관측 근거(성공 2회, ADR 0009)만으로 한다. 공지는 해석을
   돕는 주석이지 판정 근거가 아니다.
4. **관측-공지 시간 쌍은 신뢰 신호다.** UI.md 의 예(Observed 09:37 / Notice
   10:12)처럼, provider 가 Watch 관측보다 늦게 공지했는가·공지 후에도 방치했는가를
   Dataset 상세에 함께 보여준다.
5. **공개 범위.** Notice 목록·상세는 Public Read API 로 노출하고(`GET /api/v1/notices`),
   Dataset·Incident·Change 상세에는 "관련 공지" 목록으로 내려간다.

## 결과

- CLI: `kpubdata-watch notices add <url> [--title ...] [--excerpt ...]`,
  `kpubdata-watch notices link <notice-id> --incident <id> | --change <id>` 가
  P1 Official Notice manual linking 구현의 명세가 된다
  (`incidents add-notice` 는 이 형태로 일반화한다).
- Change·Incident 가 공지로 설명되는 비율은 "변화의 설명 가능성" 지표가 된다.
- 자동 후보 매칭(crawler → candidate → operator confirmation)은 향후 확장이며
  이 구조(독립 엔티티 + 링크)에서 자연스럽게 얹힌다.
