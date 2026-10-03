# ADR 0013: Overview 는 현재 스냅샷, History 는 최근 30일 — 두 화면으로 나눈다

## 상태

채택됨(Accepted) — 2026-10-03 (#108)

## 요약 (English summary)

> Overview and History become two pages that answer two different questions
> with the same rows (datasets) and different columns. Overview (`/`) answers
> "can this be used right now" with the current health and check matrix.
> History (`/history/`) answers "how reliable has this been" with a 30-day
> status grid, following the default period ADR 0010 already set. PRD §51's
> ban on a metrics dashboard (Latency, Requests, Null ratio, …) stands
> unchanged. What the ban left unstated — which visualisations are allowed at
> all — is now fixed to exactly two: (a) a status-history visualisation, any
> rendering of health or check state across time (the 30-day heatmap, the
> history strip), and (b) an evidence visualisation, any rendering of
> expected vs. observed for a single detection. Nothing outside those two
> families is in scope, however it is drawn.

## 문제

Overview 한 화면이 "지금 쓸 수 있나"(현재 상태)와 "얼마나 믿을 만했나"(30일
이력)를 함께 다뤄 왔다. 데이터셋이 늘어날수록 두 질문이 같은 공간을 다투고,
어느 쪽도 또렷하게 답하지 못한다.

동시에 `docs/UI.md`의 Charts 절(PRD §51)은 "메트릭 대시보드는 만들지 않는다"는
금지만 적어두고, 금지의 반대편 — 그래서 **무엇은** 그려도 되는가 — 를 정하지
않았다. 이 공백 때문에 PR마다 "이 시각화는 대시보드인가 아닌가"를 매번
새로 판단해야 했다(#99의 Issues First 레이아웃이 Overview 구조를 바꾼 뒤 #106이
되돌리자고 다시 연 것도 같은 공백에서 나온 되돌이표다).

## 결정

1. **Overview(`/`)는 현재 스냅샷이고, History(`/history/`)는 최근 30일이다.**
   두 페이지는 같은 행(데이터셋)에 다른 열을 쓰는 대칭 구조다 — Overview는
   현재 health와 체크 4종(A/F/C/Q) 매트릭스, History는 데이터셋 × 30일 상태
   히트맵. Dataset Detail은 지금처럼 현재 상태와 30일 이력을 함께 보여주며,
   이 ADR의 구조 변경 대상이 아니다.
2. **PRD §51의 "메트릭 대시보드 금지"는 유지한다.** Latency, Requests, Volume,
   Errors, Null Ratio 같은 시계열 메트릭 차트는 여전히 만들지 않는다.
3. **허용되는 시각화를 두 가지로 한정해 명시한다.**
   - **(a) 상태 이력 시각화** — health 또는 check 상태를 시간축에 표시하는
     모든 형태(History의 30일 히트맵, Dataset Detail의 history strip, 일자별
     비정상 데이터셋 수 막대). 그리는 값은 health/check 상태뿐이고, 상태를
     숫자로 바꾼 파생 메트릭(가동률 %, 평균 지연 등)은 그리지 않는다.
   - **(b) Evidence 시각화** — 하나의 탐지에 대한 expected vs observed 를
     그리는 모든 형태(quality 예상 구간 띠 위의 관측값 점, freshness 시간축,
     availability 실패 막대, contract 필드 diff 칩). 그리는 값은 그 탐지의
     evidence에 실제로 있는 값뿐이고, 없는 프로브나 추정값은 그리지 않는다
     (`docs/UI.md`의 Evidence-based 원칙과 동일).

   이 두 범주 밖의 시각화(메트릭 시계열, 집계 대시보드)는 금지가 그대로
   적용된다. "대시보드처럼 보이는가"를 매번 새로 판단하지 않고, "상태
   이력인가, evidence인가, 둘 다 아닌가"로 판단한다.
4. **History 기간은 ADR 0010을 따른다.** 기본 30일, API 조회 상한 90일. History
   페이지가 기본으로 보여주는 기간은 ADR 0010이 이미 정한 보존 하한(30일)과
   같다 — 이 ADR은 그 값을 UI 쪽에서 다시 확인할 뿐, 새로 정하지 않는다.

## 관계

- **#33(Status / Provider Grouped / Issues First 레이아웃 비교)**: 이 ADR은
  Overview의 **구조**(현재 스냅샷, 체크 매트릭스)를 오너 결정으로 고정한다.
  #33에 남는 범위는 이 구조 **안**에서의 나머지 layout 질문(예: Datasets
  페이지의 provider 그룹핑)과 UI Lab 프로토타입 비교다. #33은 이 ADR과
  충돌하지 않도록 범위를 조정한다.
- **#106("Issues First를 UI Lab으로 옮기고 중립 Overview로 되돌린다")**: #106의
  "중립 Overview로 되돌린다"는 방향은 이 ADR과 뒤따르는 #110(Overview를 현재
  스냅샷 + 체크 매트릭스로 바꾸는 구현)으로 **대체(superseded)**된다. Issues
  First를 UI Lab 프로토타입으로 옮기는 부분은 유효하며 #106에서 계속 진행한다.

## 결과

- `docs/UI.md`의 Charts 절과 History UX 절이 이 결정에 맞게 갱신되고, 이
  ADR을 링크한다.
- `docs/decisions/README.md`와 `mkdocs.yml` nav에 ADR 0013이 추가된다.
- 이어지는 구현 PR(#109 History 페이지, #110 Overview 스냅샷, 이후 Evidence
  미니 차트, fixture 이력 보강)이 이 ADR의 결정을 따른다.
- Read model(`api/read_models/public.py`)과 fixture 스키마는 바꾸지 않는다 —
  이 ADR은 화면 구조와 허용 시각화 범위만 정하고, 필요한 파생값(일자별 집계,
  비정상 일수 등)은 `build_demo.py`와 `presentation.py`에서 계산한다.
