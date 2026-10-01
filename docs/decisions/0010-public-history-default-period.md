# ADR 0010: 공개 History 기본 기간은 30일, 조회 상한은 90일이다

## 상태

채택됨(Accepted) — 2026-10-01 (#32, PRD §105 Q-008)

## 요약 (English summary)

> The public history view and API default to 30 days — exactly the retention
> floor for public history, because a default longer than what is guaranteed
> would lie from day 31. The API accepts `days` up to 90, the floor for
> internal metadata, so a longer honest window exists without promising it by
> default. Change and incident listings carry no period limit at all: those
> entities are kept as long as possible. Raising the default means raising the
> retention floor first.

## 문제

PRD §67 은 보존 하한만 정했다 (Public history 30일, Internal metadata 90일).
Public 화면·API 가 기본으로 보여줄 기간은 정해지지 않았다. 기본이 보존 하한보다
길면 31일째부터 빈 구간을 "이상 없음"처럼 보여주는 거짓이 되고, 짧으면 하한을
다 누리지 못한다.

## 결정

1. **기본 표시 기간은 30일이다.** Public history 의 보존 하한(30일)과 같은 값 —
   기본 뷰가 약속보다 길지 않게.
2. **API 조회 상한은 90일이다.** `GET /api/v1/datasets/{id}/history?days=N` —
   기본 30, 최대 90. Internal metadata 하한(90일)까지는 참인 데이터가 있으므로,
   늘린 창을 요청하는 사용자에게는 진실을 제공한다.
3. **Change·Incident 목록에는 기간 제한이 없다.** 이 엔티티들은 가능한 한 장기
   보관되므로(§67), 기간 파라미터는 Health·Observation timeline 에만 적용한다.
4. **기본값을 늘리려면 보존 하한을 먼저 늘린다.** 30/90 은 상한이 아니라 최소
   보증이며, 비용 실측 후 조정한다(§67). 기본 표시 ≤ 보존 하한 순서를 지킨다.

## 결과

- API_CONTRACT 의 History API 에 `days`(기본 30, 상한 90) 파라미터가 명시된다.
- UI 의 History 뷰도 같은 기본(30일)과 상한(90일) 범위 선택을 따른다.
- 조회 상한을 넘는 요청은 400 이 아니라 상한으로 잘라 응답하되 응답에
  `requested_days` 와 `effective_days` 를 남긴다 — 거짓 없이 설명 가능하게.
