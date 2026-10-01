# ADR 0008: Breaking Contract 변경의 기본 Severity 는 CRITICAL 이다

## 상태

채택됨(Accepted) — 2026-10-01 (#30, PRD §105 Q-006 — PRD §11.4 의 기본값을 확인·확정)

## 요약 (English summary)

> A breaking contract change — a field the last confirmed snapshot carried is gone,
> or a field's type changed — opens an incident at CRITICAL severity, as the PRD
> draft already defaulted. Watch exists to answer "can this data be used right
> now"; a breaking change means "not safely", so HEALTHY would be a lie. Three
> guards keep the default honest: the incident opens only after the confirmation
> probe agrees, the diff is computed against the last **confirmed** snapshot (a
> partial or empty response is an availability/quality signal, never mass field
> removal), and a dataset-specific override may lower the severity to WARNING —
> never to INFO, and only a person lowers it.

## 문제

PRD §11.4 는 Breaking (`- addr2`, `price: integer → string`) 의 기본값을
`Severity = CRITICAL` 로 두고 "Dataset-specific override 를 허용한다" 까지 적어두었지만,
이 값이 실제 구현의 기본값으로 확정되려면 근거와 경계가 필요하다:

- CRITICAL 이 과한 경우는 없는가? (선택적 필드 하나 사라진 것뿐인데?)
- CRITICAL 이 늦는 경우는 없는가? (확인 전 단일 관측으로 개시해야 하는가?)
- Override 는 어느 방향으로 어디까지 허용되는가?

## 결정

1. **기본값은 CRITICAL 을 유지한다.** Watch 가 답하는 질문은 "이 데이터를 지금
   믿고 쓸 수 있는가"다. 직전까지 있던 필드가 사라졌거나 타입이 바뀐 것은
   "그대로 쓰면 안전하지 않다"는 뜻이고, 이는 CRITICAL 의 정의 그 자체다.
   Watch 는 필드별 이용 여부를 모르므로, 소비자 보호 관점에서 기본은 강하게.
2. **확인(confirmation) 후에 개시한다.** 첫 탐지는 Change(Breaking 분류)로
   기록하고, 확인 probe 가 같은 diff 를 관측할 때 Incident 를 연다. 단일 관측의
   CRITICAL 은 false positive 를 사용자에게 노출한다(detectors README 의 Contract
   확인 규칙과 동일).
3. **Diff 의 기준은 "마지막으로 확인된 스냅샷"이다.** 실패했거나 비었거나 잘린
   응답은 Contract diff 를 만들지 않는다 — 빈 응답이 필드 전체 소실로 보이면
   안 되므로, 그런 관측은 Availability/Quality 신호로 분류된다.
4. **Override 로 낮출 수 있는 바닥은 WARNING 이다.** Dataset 마다 "이 Dataset 의
   해당 필드는 이용자가 없다"는 사정을 반영해 WARNING 까지 낮출 수 있다.
   Breaking 이 INFO 가 되는 경우는 없다(정보성 Change 는 애초에 Breaking 이
   아니다). 낮추는 것은 사람만 한다(POLICY — Review Level 하향과 같은 규칙).

## 근거

- kpubdata 0.8.0 의 datago adapter 는 한 provider 안에서 두 개의 페이지네이션
  관행(`pageNo/numOfRows` 와 odcloud 계열 `page/perPage`, catalogue `social_enterprise`
  항목)과 별도 envelope(`gyeonggi_msg`, `its_flat`) 를 함께 다룬다 — data.go.kr
  계열에서 응답 관행의 drift 가 실재한다는 코드 수준의 증거. Breaking 분류가
  가정이 아니라 실제 시나리오다.
- DOMAIN_MODEL §26 (PRD) 은 `Required field removed → CRITICAL` 를 이미 예시로
  두고 있다. 이 ADR 은 그 값을 확정하고 경계(확인 후 개시, 확인된 스냅샷 기준,
  WARNING 바닥)를 명시한 것이다.

## 결과

- Contract 검출기는 Breaking 분류 시 (a) 마지막 확인 스냅샷 대비, (b) 확인 probe
  통과 후 Incident 개시, (c) Registry 의 dataset 별 override 반영(WARNING 바닥)
  를 구현한다. fixture 테스트는 필드 제거·타입 변경·빈 응답 세 경우를 모두
  다룬다.
- Change 를 Breaking 으로 분류하는 순간의 기록(Expected·Observed·Difference·Rule·
  Evidence·Timestamp)에는 확인 probe 결과도 함께 남는다.
