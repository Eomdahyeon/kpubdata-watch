# ADR 0009: 확인 횟수는 전역 기본을 두고 Registry 가 제한적으로 조정한다

## 상태

채택됨(Accepted) — 2026-10-01 (#31, PRD §105 Q-007)

## 요약 (English summary)

> The confirmation counts stay a global default — 2 failures open an incident,
> 2 successes resolve it — and per-dataset adjustment is allowed but bounded and
> justified: a registry entry may set failures between 1 and 3 with a reason,
> while the resolve side stays fixed at 2 to keep flapping protection from
> being tuned away. What actually differs per check is **when** a confirmation
> observation can exist: availability confirms with an immediate retry, so its
> delay never depends on the probe interval; freshness and quality only observe
> on the scheduled probe, so a long-interval dataset (≥ 24h) should drop
> failures to 1 — otherwise confirming a stale daily dataset takes two more
> days.

## 문제

PRD §27 의 기본값("2 failures → OPEN, 2 successes → RESOLVE")은 모든 Dataset 에
같은 지연을 강요한다. Probe 주기가 15분인 실시간 Dataset 과 1일인 주간
Dataset 에서 "확인 2회"의 의미는 전혀 다르다:

- 실시간(15분 간격): 2 실패 = 약 30분 뒤 개시. 즉각 재시도로 확인하면 수 분.
- 주간/일간(24시간 간격): 2 실패 = **이틀 뒤** 개시. 기본값 그대로면 탐지가
  지연 자체가 된다.

반면 확인 횟수를 Dataset 마음대로 열어두면, 플래핑 방지(successes)까지 조정해
버리는 구성이 나올 수 있다.

## 결정

1. **전역 기본은 유지한다** — `failures: 2 → OPEN`, `successes: 2 → RESOLVE`.
   하나의 설명 가능한 기본이 원칙(ground rules)이다.
2. **Registry 는 `failures` 만 1~3 범위에서 조정할 수 있고 사유를 적는다.**
   `successes` 는 Dataset 이 조정하지 않는다 — 플래핑 방지는 Dataset 사정이
   아니라 시스템 성질이다.
3. **Check 종류별 확인 관측의 시점이 다름을 문서로 못박는다:**
   - Availability: 확인 probe 는 **즉시 재시도**다. 지연이 interval 에 의존하지
     않으므로 조정이 필요 없는 것이 기본이다.
   - Freshness · Quality: 확인 관측은 **다음 정기 probe**에서만 나온다(즉시
     재시도해도 데이터 상태는 그대로). `interval_minutes ≥ 1440` 이면
     `failures: 1` 을 권장한다 — 이틀 지연이 기본값이 되지 않게.
   - Contract(Breaking): 확인 probe 1회(ADR 0008 과 동일).
4. **바닥은 1이다.** `failures: 0`(한 번의 실패로 즉시 개시)은 어떤 Dataset 에서도
   허용하지 않는다(PRD §27 원칙).

## 근거

- 산술: 개시 지연 ≈ 확인 관측 확보 시간 × (failures − 1). Availability 의 즉시
  재시도는 이 값을 interval 과 무관하게 만들고, Freshness·Quality 는 interval 에
  비례하게 만든다. 24시간 주기 Dataset 에서 기본값(2)은 이틀 지연이다.
- DOMAIN_MODEL §27 의 확인 그림(detectors README)은 이미 Check 별로 확인 시점이
  다른 구조다 — 이 ADR 은 그 차이를 수치 규칙으로 못박은 것 뿐이다.

## 결과

- Registry 의 check 설정에 선택적 `confirmation: { failures: 1~3, reason: ... }`
  이 들어간다. Registry 검증은 범위(1~3)와 사유 존재를 검사한다.
- 장주기 Dataset 온보딩(#25 계열 작업) 시 `failures: 1` 권장이 선정 가이드에
  포함된다.
- Flapping 보호(successes 2)는 구현이 그 값을 상수로 둔다.
