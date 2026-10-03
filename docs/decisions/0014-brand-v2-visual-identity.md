# ADR 0014: Visual identity 는 KPubData Studio Brand v2 로 고정하고, UI Lab 은 layout 만 실험한다

## 상태

채택됨(Accepted) — 2026-10-02 (#68 — 결정 D-021 · D-022 · D-023 · D-024)

## 요약 (English summary)

> KPubData Watch uses the KPubData Studio Brand v2 visual identity unchanged: the
> same K symbol and lockup hierarchy, the same colour tokens, light as the
> canonical theme with dark as an alternative, Studio's typography, density and
> accessibility rules. The UI Lab experiments with information architecture and
> layout only — never with the brand palette, logo, typography or status
> semantics — so a comparison of layouts is not skewed by visual differences.
> Brand colour and status colour are separate systems; Fresh Mint is never
> Healthy. The tokens come from one file copied verbatim from Studio at a pinned
> commit, and a gate fails on drift.

## 문제

PRD §33 은 UI 에서 고정하지 않을 것에 "색상 세부 규칙" 을 넣었다 (D-012 는 UI 를 UI Lab 에서
실험한다고 정했다). 이대로 구현하면 Watch 가 KPubData Studio 와 다른 팔레트 · 로고 · 타이포그래피 ·
상태 표현을 갖게 되어, 같은 KPubData 제품군이 서로 다른 제품처럼 보인다. 또 UI Lab 의 세 layout
이 서로 다른 색과 글꼴을 쓰면, 비교 결과가 정보구조가 아니라 시각 차이에 좌우된다.

Studio 는 이미 Brand v2 (studio#628) 로 canonical visual spec 을 정했다 — 같은 minimal geometric K
심볼, `KPubData` 가 주인공인 lockup, light canonical, 브랜드색과 상태색의 분리.

## 결정

- **D-021** KPubData Watch는 KPubData Studio Brand v2와 동일한 visual identity를 사용한다.
- **D-022** UI Lab에서 실험하는 것은 information architecture와 layout이며, brand palette / logo / typography / status semantics는 실험하지 않는다.
- **D-023** Light theme를 canonical visual baseline으로 사용한다. Dark mode는 alternative user theme다.
- **D-024** Brand color와 status color를 분리한다. Fresh Mint를 Healthy 표현에 사용하지 않는다.

D-022 는 D-012 를 좁힌다: UI 는 여전히 UI Lab 에서 실험하지만, 실험 대상은 layout 이고 visual
identity 가 아니다.

## 결과

- Watch 의 시각 규칙은 [시각 정체성](../VISUAL_IDENTITY.md), 고정/실험 구분은 [UI](../UI.md) 의
  "고정된 visual identity 와 실험하는 layout" 에 있다.
- 토큰 소스는 하나다: `src/kpubdata_watch/web/static/brand-v2.css` — Studio `src/globals.css` 의
  블록을 commit 고정으로 그대로 복사했다. UI Lab 은 버릴 수 있으므로(D-012) 원본은 Public Status
  쪽에 둔다.
- Healthy · Degraded · Critical · Unknown 은 Studio 의 `--status-success` · `--status-warning` ·
  `--status-failure` · `--status-unknown` 이고, 아이콘과 글자를 함께 쓴다.
- `scripts/check_brand_tokens.py` 가 문서와 토큰 파일의 불일치, 브랜드 토큰과 상태 토큰의 값 충돌,
  Health 대비 4.5:1 미만, UI Lab · `web/` 의 토큰 재정의에 실패하고, Studio 의 `globals.css` 를 주면
  값 drift 에도 실패한다. CI 가 Studio 를 직접 비교하는 job 은 #72 에서 다룬다.
- Watch 는 새 로고 · 팔레트 · 상태색을 만들지 않는다. Studio 와 다르면 Studio 가 맞다.
