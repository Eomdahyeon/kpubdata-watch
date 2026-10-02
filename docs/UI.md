# UI

> 이 문서는 KPubData Watch MVP PRD(v1.0 Draft, 2026-09-30)의 §33, §34, §35, §36, §37, §38, §39, §40, §41, §42, §43, §44, §45, §46, §47, §48, §49, §50, §51, §52, §53, §54, §55 를 목적별로 나눈 것이다. 전체 대응표는 [문서 안내](index.md#prd) 에 있다.

## UI Strategy

<small>PRD §33</small>

UI는 MVP 개발과 동시에 **실험 가능하게 유지한다.**

중요한 원칙:

> Backend Domain Model과 UI Layout을 결합하지 않는다.

고정할 것:

```text
Dataset
Observation
Detection
Change
Incident
Health
History
```

고정하지 않을 것:

```text
Card vs Table

Provider accordion 여부

Active Issues 위치

30/90 day status bar 형태

Dashboard 형태

Chart 종류
```

### 고정된 visual identity 와 실험하는 layout

<small>#68</small>

PRD §33 은 "색상 세부 규칙" 도 고정하지 않는 쪽에 두었다. #68 에서 이를 바꿨다: **visual identity 는
고정하고, layout 만 실험한다.** 같은 KPubData 제품군이 다른 제품처럼 보이지 않게 하고, UI Lab 의
비교가 색 · 글꼴 차이로 오염되지 않게 하기 위해서다.

| 고정 — KPubData Studio Brand v2 와 같다 | 실험 — UI Lab (#33) |
|---|---|
| Logo geometry · lockup hierarchy (`KPubData` + 중립 `Watch`) | Status vs Provider-grouped vs Issues-first |
| Color tokens (`src/kpubdata_watch/web/static/brand-v2.css`) | Card vs compact table |
| Light canonical / dark 대체 테마 | Issue 위치 |
| Typography · spacing · radius · surface | 30/90-day history 시각화 |
| 상태색 의미 (Health → Studio status token) | Filter 위치 |
| 접근성 · 대비 기준 | Dataset 목록 밀도 |

Canonical 기준은 Studio 의
[docs/brand/VISUAL_IDENTITY.md](https://github.com/yeongseon/kpubdata-studio/blob/1fbf57e41a32b3ef9cd353666beb1fcd0d6b97e9/docs/brand/VISUAL_IDENTITY.md)
와 [src/globals.css](https://github.com/yeongseon/kpubdata-studio/blob/1fbf57e41a32b3ef9cd353666beb1fcd0d6b97e9/src/globals.css) 다 (commit
고정). Watch 에 적용하는 규칙은 [시각 정체성](VISUAL_IDENTITY.md) 에 있고, 아래 §52 · §53 은 그 문서가
우선한다. Watch 는 새 로고 · 팔레트 · 상태색을 만들지 않는다.

## UI Architecture

<small>PRD §34</small>

```text
Database
   ↓
Domain
   ↓
Read Model
   ↓
Public API
   ↓
┌───────────────┬────────────────┬───────────────┐
│ Status UI     │ Provider UI    │ Issues UI     │
└───────────────┴────────────────┴───────────────┘
```

UI가 DB Table을 직접 해석하지 않는다.

## UI Read Model

<small>PRD §35</small>

예:

```json
{
  "dataset_id": "visitkorea-tourism",

  "name": "한국관광공사 관광정보",
  "provider": "한국관광공사",

  "health": "healthy",

  "checks": {
    "availability": "pass",
    "freshness": "pass",
    "contract": "pass",
    "quality": "pass"
  },

  "active_issue": null,

  "latest_change": {
    "type": "contract",
    "severity": "info",
    "occurred_at": "2026-09-29T14:20:00+09:00"
  },

  "last_checked_at": "2026-09-30T21:10:00+09:00"
}
```

같은 Read Model로 여러 UI를 시험한다.

## UI Lab

<small>PRD §36</small>

Production UI와 별도로 UI 실험 공간을 둔다.

```text
ui-lab/
```

UI Lab은 언제든 버릴 수 있어야 한다.

Watch Engine은 UI Lab에 의존하면 안 된다.

모든 prototype 은 같은 토큰 파일 `src/kpubdata_watch/web/static/brand-v2.css` 를 링크하고, 토큰을
스스로 정의하지 않는다 (#68). `scripts/check_brand_tokens.py` 가 `ui-lab/` 아래 CSS · HTML 이 토큰을
다시 정의하면 실패한다.

## UI Lab Fixtures

<small>PRD §37</small>

반드시 다음 Fixture를 만든다.

```text
10-datasets.json
50-datasets.json
150-datasets.json

all-healthy.json

mixed-health.json

active-incidents.json

contract-changes.json

freshness-delay.json

provider-outage.json

unknown-monitoring.json
```

이를 통해 Dataset 규모가 커져도 UI가 유지되는지 검증한다.

## UI Experiment A — Status Page

<small>PRD §38</small>

```text
KPubData Watch

Public Data Health

47 Healthy
2 Degraded
1 Unknown

────────────────────────

한국관광공사 관광정보
Healthy

서울 버스정보
Degraded
Freshness delayed

...
```

장점:

```text
직관적
익숙함
MVP 구현 쉬움
```

## UI Experiment B — Provider Group

<small>PRD §39</small>

```text
한국관광공사
8 Healthy

국토교통부
15 Healthy · 1 Degraded

  아파트 실거래가
  Healthy

  공동주택 기본정보
  Healthy

  지하안전정보
  Degraded
```

Dataset이 50~150개 이상으로 증가했을 때 검증한다.

## UI Experiment C — Issue First

<small>PRD §40</small>

```text
Active Issues

CRITICAL
국토교통부 ○○ API
Breaking contract change

WARNING
서울 버스정보
Freshness delayed 42m

────────────────────────

All Datasets
...
```

운영자/개발자에게는 이 구조가 더 효율적일 수 있다.

## UI Evaluation Criteria

<small>PRD §41</small>

각 UI Prototype을 다음 기준으로 비교한다.

```text
1. 5초 안에 문제가 있는 Dataset을 찾을 수 있는가?

2. 10 Dataset에서도 자연스러운가?

3. 50 Dataset에서도 탐색 가능한가?

4. 150 Dataset에서도 화면이 무너지지 않는가?

5. Provider별 문제를 인지하기 쉬운가?

6. Healthy Dataset 때문에 문제 Dataset이 묻히지 않는가?

7. Health와 Change를 혼동하지 않는가?

8. UNKNOWN을 장애로 오인하지 않는가?

9. 모바일에서도 핵심 상태 확인이 가능한가?

10. 판정 근거로 자연스럽게 Drill-down할 수 있는가?
```

UI 선택은 구현 편의가 아니라 이 기준으로 결정한다.

## Public Status Information Architecture

<small>PRD §42</small>

MVP Production UI 최소 구조:

```text
/
Public Status

/datasets/{dataset_id}
Dataset Detail

/incidents/{incident_id}
Incident Detail

/changes/{change_id}
Change Detail
```

UI Lab은 별도:

```text
/lab/status
/lab/provider
/lab/issues
```

Production deployment에서는 UI Lab 비활성화 가능해야 한다.

## Public Status Page

<small>PRD §43</small>

첫 화면 목표:

> **현재 문제가 있는 Dataset을 빠르게 찾는다.**

상단은 단일 "All systems operational"보다 Distribution을 우선한다.

예:

```text
Public Data Health

100 monitored datasets

96 Healthy
 2 Degraded
 1 Critical
 1 Unknown
```

이렇게 해야 한 Dataset 문제 때문에:

```text
"한국 공공데이터가 장애입니다."
```

처럼 과도하게 표현하는 것을 피할 수 있다.

## Search / Filtering

<small>PRD §44</small>

Dataset 수가 증가할 것을 고려해 Read API부터 지원 가능하게 설계한다.

향후 UI Filter:

```text
Search

Provider

Health

Check

Category
```

예:

```text
Provider = 국토교통부

Health = Degraded

Check = Freshness

Category = 부동산
```

MVP 10 Dataset에서는 UI에 전부 노출하지 않아도 된다.

## Provider Grouping

<small>PRD §45</small>

기본 Group 후보는 Provider다.

```text
Provider
   ↓
Dataset
```

Category:

```text
부동산
관광
교통
통계
환경
금융
```

은 기본 Group보다는 Filter 용도로 사용한다.

Provider 상태 자체를 하나의 색으로 단순화하지 않는다.

예:

```text
국토교통부

28 Healthy
1 Degraded
1 Unknown
```

Provider 전체 장애가 확인된 경우에만 Provider Incident를 별도로 검토한다.

## Dataset List Density

<small>PRD §46</small>

정상 Dataset에서는 세부 Check를 모두 노출하지 않는다.

권장:

```text
한국관광공사 관광정보

Healthy

Checked 3m ago
```

문제가 있는 경우에만 이유를 노출한다.

```text
서울 버스정보

Degraded

Freshness delayed 42m

Checked 2m ago
```

Change만 있는 경우:

```text
조달청 물품목록정보

Healthy

ⓘ Contract changed

Checked 5m ago
```

원칙:

> **Healthy일 때는 단순하게, 문제가 있을 때만 자세하게.**

## Dataset Detail

<small>PRD §47</small>

목표:

> 왜 이 Dataset이 현재 Health 상태인지 설명한다.

예:

```text
한국관광공사
국문 관광정보 API

HEALTHY

Last checked
21:12:43 KST

Last successful
21:12:43 KST

────────────────────────

Checks

Availability
PASS

Freshness
PASS

Contract
PASS

Quality
PASS

────────────────────────

Recent Changes

Sep 29 14:20
Contract changed
+ productEngName

────────────────────────

Recent Incidents

None
```

## Why Was This Detected?

<small>PRD §48</small>

모든 Warning/Critical 결과에는 이 UI를 제공한다.

예:

```text
Freshness delayed

Why was this detected?

Expected
09:00 ± 30 min

Observed
latest data = 07:58

Checked
09:37

Difference
1h 39m

Rule
Expected update window exceeded
```

KPubData Watch UI의 핵심 원칙이다.

## Contract Diff UX

<small>PRD §49</small>

기본 화면:

```text
Contract Change

Added

+ productEngName    string
+ manufacturerCode string


Removed

- addr2             string


Changed

~ price
  integer → string
```

기본은 Human-readable Diff다.

추가:

```text
View raw schema
View raw diff
```

형태로 기술 근거를 제공한다.

원칙:

```text
Human-readable first
Raw evidence second
```

## History UX

<small>PRD §50</small>

Dataset Detail에는 시간 흐름을 제공한다.

예:

```text
Sep 30 21:12
Healthy

Sep 30 20:12
Healthy

Sep 30 19:12
Healthy

Sep 29 14:20
Contract changed

Sep 27 09:37
Freshness delayed

Sep 27 10:21
Recovered
```

Watch의 장기 자산은 단순 현재 상태가 아니라 History다.

## Charts

<small>PRD §51</small>

Chart는 최소화한다.

MVP에서 다음과 같은 Dashboard는 만들지 않는다.

```text
Requests
Latency
Volume
Errors
Availability
Freshness
Null Ratio
...
```

대신 의미를 우선한다.

예:

```text
Volume

10,124 records

Expected range
9,850–10,420

PASS
```

추후 필요 시 Sparkline을 추가할 수 있다.

## Visual Design Principles

<small>PRD §52</small>

> 구체적인 값(radius 8px, 36px 행, 20px page title, 글꼴)은 [시각 정체성](VISUAL_IDENTITY.md) §5 —
> Studio Brand v2 — 가 정한다. 아래는 PRD 원문의 방향이다.

UI 톤:

```text
Status Page
+
Developer Infrastructure
+
Data Observability
```

피해야 하는 방향:

```text
화려한 BI Dashboard
Marketing-heavy SaaS Landing
복잡한 Azure Portal식 화면
```

기본:

```text
Light background
Simple border
Minimal shadow

8–12px radius

8px spacing grid

System/Pretendard-like sans serif

Technical values
monospace optional
```

## Color Semantics

<small>PRD §53</small>

> 색 값과 토큰은 [시각 정체성](VISUAL_IDENTITY.md) §4 가 정한다: Healthy · Degraded · Critical ·
> Unknown 은 Studio 의 `--status-success` · `--status-warning` · `--status-failure` ·
> `--status-unknown` 이다. Informational Change 는 **중립**이다 — Brand Blue 는 상호작용 색이라
> 아래 원문의 "Blue" 는 쓰지 않는다. Brand Blue · Data Cyan · Fresh Mint 는 상태를 나타내지 않는다.

색상만으로 상태를 표현하지 않는다.

텍스트 + 아이콘 + 색상을 함께 사용한다.

의미:

```text
Healthy
Green

Degraded
Yellow / Amber

Critical
Red

Unknown
Gray

Informational Change
Blue / Neutral
```

접근성을 위해:

```text
● Healthy

▲ Degraded

✕ Critical

? Unknown

ⓘ Change
```

등의 시각적 단서를 함께 제공한다.

## Time UX

<small>PRD §54</small>

상대시간과 정확한 시간을 함께 제공한다.

기본:

```text
3 min ago
```

상세/Tooltip:

```text
2026-09-30 21:12:43 KST
```

Incident/History에서는 정확한 시간을 기본으로 표시한다.

## Official Notice

<small>PRD §55</small>

MVP P0에서는 자동 공지 Crawling을 요구하지 않는다.

초기:

```text
Operator manually attaches official notice URL
```

Incident:

```text
Observed
09:37

Official Notice
10:12
```

처럼 보여줄 수 있다.

향후:

```text
Notice crawler
      ↓
Candidate matching
      ↓
Operator confirmation
      ↓
Explain
```

으로 확장한다.
