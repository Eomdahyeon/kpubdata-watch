# 시각 정체성 (Visual Identity)

> KPubData Watch 는 **KPubData Studio Brand v2** 를 시각 정체성으로 그대로 쓴다 (#68).
> Watch 는 새 로고 · 새 팔레트 · 새 상태색을 만들지 않는다. 이 문서는 Studio 규칙을 Watch 화면
> (Public Status · UI Lab) 에 옮길 때 필요한 것만 적고, 나머지는 Studio 문서를 가리킨다.
>
> 핵심 원칙: **같은 제품군의 같은 visual identity, 다른 product information architecture.**

## 1. Canonical source

Studio 가 기준이고 Watch 는 따라간다. 아래 링크는 Watch 토큰을 복사한 Studio commit
`1fbf57e41a32b3ef9cd353666beb1fcd0d6b97e9` 에 고정돼 있다.

| 무엇 | Studio 문서 |
|---|---|
| 규칙 (색 값 · token · 크기 · 금지 사항) | [docs/brand/VISUAL_IDENTITY.md](https://github.com/kpubdata-lab/kpubdata-studio/blob/1fbf57e41a32b3ef9cd353666beb1fcd0d6b97e9/docs/brand/VISUAL_IDENTITY.md) |
| 의도 (왜 이렇게 생겼나) | [docs/brand/DESIGN_CONCEPT.md](https://github.com/kpubdata-lab/kpubdata-studio/blob/1fbf57e41a32b3ef9cd353666beb1fcd0d6b97e9/docs/brand/DESIGN_CONCEPT.md) |
| 토큰 값 | [src/globals.css](https://github.com/kpubdata-lab/kpubdata-studio/blob/1fbf57e41a32b3ef9cd353666beb1fcd0d6b97e9/src/globals.css) |
| 로고 자산 | [assets/logo/kpubdata-brand-assets/](https://github.com/kpubdata-lab/kpubdata-studio/blob/1fbf57e41a32b3ef9cd353666beb1fcd0d6b97e9/assets/logo/kpubdata-brand-assets/README.md) |

Watch 쪽에서 이 값을 담는 곳은 **한 파일**이다.

```text
src/kpubdata_watch/web/static/brand-v2.css
```

- Studio `src/globals.css` 의 light · dark · OS-dark custom-property 블록을 **글자 그대로** 복사했다.
  파일 머리에 원본 경로와 commit 이 있다.
- Public Status(서버 렌더링, `web/`) 는 이 파일을 static 으로 제공하고, UI Lab 의 모든 prototype
  (`ui-lab/status-page`, `ui-lab/provider-grouped`, `ui-lab/issues-first`) 은 이 파일을 링크한다.
  prototype 이나 template 이 토큰을 다시 정의하지 않는다.
- 토큰 파일이 `ui-lab/` 이 아니라 `web/static/` 에 있는 이유: UI Lab 은 언제든 버릴 수 있고 Watch
  Engine 은 UI Lab 에 의존하지 않는다 (ADR 0005, D-012). 버려지지 않는 쪽(패키지에 포함되는
  Public Status)이 원본을 갖고, 버려질 수 있는 쪽이 그것을 참조한다.

**Studio 와 다르면 Studio 가 맞다.** Watch 에서 값을 고치지 않는다. Studio 가 바뀌면 블록을 다시
복사하고, 파일 머리의 commit · 이 문서의 링크 · §4 표를 함께 바꾼다 (§8).

## 2. 무엇을 고정하고 무엇을 실험하나

```text
고정 (Studio 와 같다)                실험 (Watch UI Lab, #33)
─────────────────────               ────────────────────────
Logo geometry                       Status vs Provider-grouped vs Issues-first
Brand lockup hierarchy              Card vs compact table
Color tokens                        Issue placement
Light / dark theme semantics        30/90-day history visualization
Typography                          Filter placement
Spacing / radius / surface language Dataset-list density
Status-color semantics
Accessibility contrast rules
```

UI Lab 의 세 layout 은 **같은 토큰 파일과 같은 규칙**을 쓴다. 비교 결과가 색이나 글꼴 차이로
오염되지 않게 하기 위해서다. layout 실험은 [UI](UI.md) 가 다룬다.

## 3. 로고와 lockup

- 심볼은 Studio 와 **같은 minimal geometric K** 다 — Studio 자산(`symbol_light.svg` 등)을 그대로 쓴다.
  Watch 전용 심볼, 변형 geometry, gradient · glow · shadow 를 만들지 않는다 (Studio §2.1).
- Lockup 은 **K 심볼 + `KPubData` + `Watch`** 다.

| 요소 | light 표면 | dark 표면 |
|---|---|---|
| `KPubData` (Pretendard 700, 주인공) | Ink `#172033` | White `#FFFFFF` |
| `Watch` suffix (작고 · 가볍고 · 중립색) | Slate `#64748B` | `#94A3B8` |

- `Watch` 는 `KPubData` 보다 강해 보이면 안 되고, 브랜드색(Blue · Cyan · Mint)을 쓰지 않는다 (Studio §2.3).
- 한 화면에 제품명은 한 번이다. minimum size(심볼 16px, 가로 lockup 높이 20px) 와 clear space(심볼
  높이의 ½) 는 Studio §2.1 을 따른다.
- Studio 자산에는 아직 `KPubData Watch` lockup 파일이 없다. 화면 코드가 생길 때 Studio 의 심볼 SVG
  와 위 텍스트 규칙으로 조합한다. 새 자산이 필요하면 Studio 저장소에 요청한다 — Watch 가 만들지 않는다.

## 4. 색

### 4.1 Light 가 canonical, dark 는 대체 테마

- **Light theme 가 canonical** 이다. 스크린샷 · README · visual review 의 기준은 light 다.
- Dark 는 같은 의미 체계(역할 · 상태 대응 · 정보 위계)를 유지하고 값만 바꾼 **대체 테마**다.
  순수한 검정 `#000000` 을 쓰지 않는다 (Studio §3.4).
- 테마 선택은 Studio 와 같다: `<html data-theme="light|dark">`, 속성이 없으면 OS 설정
  (`prefers-color-scheme`) 을 따른다.

### 4.2 토큰 표

아래 표는 `brand-v2.css` 의 light · dark 값과 같아야 한다. `scripts/check_brand_tokens.py` 가 다르면
실패한다.

<!-- brand-v2-tokens:start -->
| 토큰 | light | dark |
|---|---|---|
| `--brand-primary` | `#2563eb` | `#2563eb` |
| `--brand-primary-foreground` | `#ffffff` | `#ffffff` |
| `--brand-subtle` | `#eaf1fe` | `#1e2836` |
| `--brand-text` | `var(--brand-primary)` | `#60a5fa` |
| `--data-accent` | `#06b6d4` | `#06b6d4` |
| `--data-accent-strong` | `#0891b2` | `#06b6d4` |
| `--brand-secondary` | `#14b8a6` | `#14b8a6` |
| `--brand-secondary-strong` | `#0d9488` | `#14b8a6` |
| `--background` | `#f7f8f3` | `#15171a` |
| `--foreground` | `#172033` | `#e8eaed` |
| `--card` | `#ffffff` | `#1c1f23` |
| `--card-foreground` | `#172033` | `#e8eaed` |
| `--muted` | `#f1f3ef` | `#23272c` |
| `--muted-foreground` | `#5e6e84` | `#9aa3ae` |
| `--border` | `#e5e7e2` | `#2e3238` |
| `--input` | `#d5d9d2` | `#3a3f46` |
| `--ring` | `var(--brand-primary)` | `#60a5fa` |
| `--sidebar` | `#f1f4f4` | `#1a1d21` |
| `--sidebar-foreground` | `#172033` | `#e8eaed` |
| `--sidebar-muted` | `#5e6e84` | `#9aa3ae` |
| `--sidebar-border` | `#e5e7e2` | `#2a2e34` |
| `--sidebar-hover` | `#e6eaea` | `#23272c` |
| `--sidebar-active` | `#eaf1fe` | `#1e2836` |
| `--sidebar-active-foreground` | `var(--brand-primary)` | `#60a5fa` |
| `--status-success` | `#15803d` | `#4ade80` |
| `--status-success-subtle` | `#dcfce7` | `#052e16` |
| `--status-success-border` | `#86efac` | `#166534` |
| `--status-warning` | `#b45309` | `#fbbf24` |
| `--status-warning-subtle` | `#fef3c7` | `#422006` |
| `--status-warning-border` | `#fcd34d` | `#92400e` |
| `--status-failure` | `#b91c1c` | `#f87171` |
| `--status-failure-subtle` | `#fee2e2` | `#450a0a` |
| `--status-failure-border` | `#fca5a5` | `#991b1b` |
| `--status-unknown` | `#52525b` | `#a1a1aa` |
| `--status-unknown-subtle` | `#f4f4f5` | `#27272a` |
| `--status-unknown-border` | `#d4d4d8` | `#3f3f46` |
| `--status-success-solid` | `#15803d` | `#16a34a` |
| `--status-warning-solid` | `#b45309` | `#d97706` |
| `--status-failure-solid` | `#b91c1c` | `#dc2626` |
| `--status-unknown-solid` | `#52525b` | `#71717a` |
<!-- brand-v2-tokens:end -->

`--sidebar-*` 는 Studio 의 사이드바 영역 이름이다. Watch 에 사이드바가 없어도 값은 그대로 둔다 —
고르지 않고 통째로 복사해야 drift 비교가 단순하다.

### 4.3 브랜드 색과 상태 색은 다른 체계다

| 색 | 토큰 | Watch 에서 쓴다 | 쓰지 않는다 |
|---|---|---|---|
| Brand Blue `#2563EB` | `--brand-primary` · `--brand-text` · `--ring` | 링크 · 선택된 필터/탭 · focus ring · 주 동작 하나 | **상태 표시** · 넓은 배경 · `Watch` suffix |
| Data Cyan `#06B6D4` | `--data-accent` · `--data-accent-strong` | 차트 · 히스토리의 데이터 강조 (마크는 `-strong`) | **상태 표시** · 링크 · CTA |
| Fresh Mint `#14B8A6` | `--brand-secondary` · `--brand-secondary-strong` | 보조 데이터 시리즈 · 작은 디테일 | **Healthy · success** · 버튼 · 넓은 면 |

- **Brand Blue · Data Cyan · Fresh Mint 는 어떤 Health · Check 상태도 나타내지 않는다.**
  특히 Fresh Mint 는 Healthy 가 아니다.
- 화면 대부분은 중립 표면(Canvas · Surface · Border)이다.
- `check_brand_tokens.py` 가 light · dark 모두에서 브랜드 토큰 값이 어떤 `--status-*` 값과도 같지
  않은지 검사한다 (Studio `visualTokensGate` 와 같은 규칙).

### 4.4 Health · Check 상태 → Studio status 토큰

Watch 의 Health ([도메인 모델](DOMAIN_MODEL.md)) 는 Studio 의 status 토큰으로만 칠한다. 새 상태
토큰을 만들지 않는다.

<!-- health-status-map:start -->
| Health | 토큰 | 아이콘 | 글자 |
|---|---|---|---|
| Healthy | `--status-success` | ● | `Healthy` |
| Degraded | `--status-warning` | ▲ | `Degraded` |
| Critical | `--status-failure` | ✕ | `Critical` |
| Unknown | `--status-unknown` | ? | `Unknown` |
<!-- health-status-map:end -->

- 배경 · 테두리 · 채운 배지는 같은 계열의 `-subtle` · `-border` · `-solid` 를 쓴다.
- Check 결과도 같은 체계다: `PASS` → success, `WARN` → warning, `FAIL` → failure, `UNKNOWN` → unknown.
  `NOT_APPLICABLE` 은 상태가 아니므로 중립(`--muted-foreground`) 이다.
- **Informational Change 는 중립**(`--muted-foreground` + ⓘ) 이다. PRD §53 의 "Blue / Neutral" 중
  Blue 는 쓰지 않는다 — Brand Blue 는 상호작용 색이라 상태처럼 읽히면 안 된다.
- **색만으로 상태를 전달하지 않는다.** 모든 상태 표시는 아이콘 + 글자 + 색을 함께 쓴다. Unknown 은
  Watch 가 관측하지 못했다는 뜻이고, 0 이나 Critical 이 아니다 (AGENTS.md).

## 5. 타이포그래피 · 밀도 · 표면

Studio §4–§5 와 같다. Studio 는 이 값을 Tailwind `@theme` 블록에 두므로 `brand-v2.css`(일반 CSS
custom property) 에는 들어 있지 않다. Watch 화면 코드가 생기면 아래 값을 그대로 쓴다.

| 용도 | 값 |
|---|---|
| Wordmark | Pretendard 700 |
| Page title (가장 큰 글자) | 600 20/28 |
| Section title | 600 14/20 |
| Body | 400 14/20 |
| Table | 400 13/18, 숫자는 `tabular-nums` · 오른쪽 정렬 |
| Metadata · 시간 | 400 12/16 |
| Code · 식별자 (dataset id, field, run id) | 400 13/18 monospace |
| 본문 글꼴 | `ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans KR", sans-serif` |

- 표 행 높이 36px, 카드 간격 12px, 모서리 8px.
- 표면 구분은 Border 로 한다. 그림자는 쓰지 않거나 아주 옅게만 쓴다.
- 큰 마케팅 헤딩을 쓰지 않는다. generic SaaS · BI dashboard 가 아니라 전문 data tool 처럼 보인다.
- 값을 모르면 `0` 이 아니라 `—` 로 쓴다.

## 6. 접근성

Studio 기준을 그대로 쓴다.

| 항목 | 기준 |
|---|---|
| 대비 (Studio §3.5, #631) | 텍스트 4.5:1, 큰 텍스트 · 비텍스트(차트 마크 · focus ring · 아이콘) 3:1. Health 상태 글자는 아래 §6.1 처럼 계산해서 검사한다 |
| 390px | 390px 폭에서 페이지 가로 스크롤이 없다. 넓은 표는 카드 안에서만 스크롤한다 (Studio §5) |
| Reduced motion | `prefers-reduced-motion: reduce` 에서 animation · transition 을 끈다 (Studio `globals.css` 의 reduced-motion 규칙). 상태 점이 깜박여도 옆에 글자가 있으므로 정보는 사라지지 않는다 |
| 색에 의존하지 않기 | §4.4 — 아이콘 + 글자 + 색 |

### 6.1 Health 상태 글자의 대비

네 Health 상태 글자색(`--status-*`) 을 세 배경 — 자기 `-subtle` 배경(배지), `--card`, `--background`
— 위에서 light · dark 로 계산한 WCAG 2.1 대비다 (4 × 3 × 2 = 24 쌍). 아래 표는
`python scripts/check_brand_tokens.py --contrast` 의 출력을 그대로 붙였다. `check_brand_tokens.py` 가
한 쌍이라도 4.5:1 미만이면 실패하고, 이 표가 계산 결과와 다르면 실패한다.

<!-- health-contrast:start -->
| theme | Health | 글자 | 배경 | 대비 |
|---|---|---|---|---|
| light | Healthy | `--status-success` `#15803d` | `--status-success-subtle` `#dcfce7` | 4.57:1 |
| light | Healthy | `--status-success` `#15803d` | `--card` `#ffffff` | 5.02:1 |
| light | Healthy | `--status-success` `#15803d` | `--background` `#f7f8f3` | 4.70:1 |
| light | Degraded | `--status-warning` `#b45309` | `--status-warning-subtle` `#fef3c7` | 4.51:1 |
| light | Degraded | `--status-warning` `#b45309` | `--card` `#ffffff` | 5.02:1 |
| light | Degraded | `--status-warning` `#b45309` | `--background` `#f7f8f3` | 4.71:1 |
| light | Critical | `--status-failure` `#b91c1c` | `--status-failure-subtle` `#fee2e2` | 5.30:1 |
| light | Critical | `--status-failure` `#b91c1c` | `--card` `#ffffff` | 6.47:1 |
| light | Critical | `--status-failure` `#b91c1c` | `--background` `#f7f8f3` | 6.06:1 |
| light | Unknown | `--status-unknown` `#52525b` | `--status-unknown-subtle` `#f4f4f5` | 7.03:1 |
| light | Unknown | `--status-unknown` `#52525b` | `--card` `#ffffff` | 7.73:1 |
| light | Unknown | `--status-unknown` `#52525b` | `--background` `#f7f8f3` | 7.24:1 |
| dark | Healthy | `--status-success` `#4ade80` | `--status-success-subtle` `#052e16` | 8.55:1 |
| dark | Healthy | `--status-success` `#4ade80` | `--card` `#1c1f23` | 9.49:1 |
| dark | Healthy | `--status-success` `#4ade80` | `--background` `#15171a` | 10.31:1 |
| dark | Degraded | `--status-warning` `#fbbf24` | `--status-warning-subtle` `#422006` | 8.73:1 |
| dark | Degraded | `--status-warning` `#fbbf24` | `--card` `#1c1f23` | 9.91:1 |
| dark | Degraded | `--status-warning` `#fbbf24` | `--background` `#15171a` | 10.76:1 |
| dark | Critical | `--status-failure` `#f87171` | `--status-failure-subtle` `#450a0a` | 5.84:1 |
| dark | Critical | `--status-failure` `#f87171` | `--card` `#1c1f23` | 5.98:1 |
| dark | Critical | `--status-failure` `#f87171` | `--background` `#15171a` | 6.49:1 |
| dark | Unknown | `--status-unknown` `#a1a1aa` | `--status-unknown-subtle` `#27272a` | 5.81:1 |
| dark | Unknown | `--status-unknown` `#a1a1aa` | `--card` `#1c1f23` | 6.45:1 |
| dark | Unknown | `--status-unknown` `#a1a1aa` | `--background` `#15171a` | 7.01:1 |
<!-- health-contrast:end -->

가장 낮은 쌍은 light Degraded — `#b45309` on `#fef3c7` = 4.51:1 — 로, 기준을 넘지만 여유가 거의 없다.
Studio 가 이 값을 바꾸면 이 gate 가 먼저 알려 준다.

## 7. 문서 사이트

이 문서 사이트(MkDocs Material) 도 Brand v2 를 따른다: Studio 문서 사이트처럼 header 는 흰색이고
링크 · accent 만 Brand Blue 다 (`docs/stylesheets/brand.css`). dark 의 파랑 텍스트는 `#60A5FA` 다.

## 8. Drift 검증

`scripts/check_brand_tokens.py` 가 기계적으로 검사한다.

| 언제 | 무엇을 | 어디서 |
|---|---|---|
| 항상 (offline) | 토큰 파일의 세 블록, OS-dark = dark, light 의 핵심 역할이 Studio §3.1 팔레트(Blue · Cyan · Mint · Ink · Canvas · Surface · Border) 와 같음, 브랜드 ↔ 상태 분리, Health 대비 24 쌍 ≥ 4.5:1 과 §6.1 표 = 계산 결과, §4.2 표 = 토큰 파일, §4.4 의 네 Health 가 정의된 `--status-*` 토큰, `docs/` 의 고정 Studio 링크 = 토큰 파일 머리의 commit, `ui-lab/` · `web/` 의 다른 CSS · HTML · template 이 토큰을 다시 정의하지 않음 | `tests/unit/scripts/test_check_brand_tokens.py` 가 이 저장소에 대해 실행하므로 CI 의 pytest 가 gate 다 |
| Studio 를 줄 때 | 세 블록의 모든 토큰 값이 Studio `src/globals.css` 와 같음 | `STUDIO_GLOBALS_CSS=<Studio 의 globals.css> python scripts/check_brand_tokens.py` 또는 `--studio <path>` |

offline 검사는 Watch 안의 일관성만 본다. Studio 가 바뀌었는지는 Studio 파일을 줘야 알 수 있다 —
CI 는 Studio 저장소를 가져오지 않으므로 이 비교는 사람이 (또는 Studio 변경을 따라가는 작업에서)
돌린다.

Studio 를 따라가는 순서:

1. Studio 의 `src/globals.css` 로 `--studio` 비교를 돌린다. 실패하면 Studio 가 바뀐 것이다.
2. 세 블록을 `brand-v2.css` 로 다시 복사하고 머리의 commit 을 바꾼다.
3. §4.2 표와 이 문서의 Studio 링크 commit 을 바꾼다.
4. `python scripts/check_brand_tokens.py` 와 `pytest` 를 통과시킨다.
