# Quality — Volume · Completeness

> 이 문서는 KPubData Watch MVP PRD(v1.0 Draft, 2026-09-30)의 §11.5, §11.6, §11.7 를 목적별로 나눈 것이다. 전체 대응표는 [문서 안내](../index.md#prd) 에 있다.

## Quality

<small>PRD §11.5</small>

Quality는 하위 Check를 묶는 상위 Dimension이다.

초기:

```text
Quality
├── Volume
└── Completeness
```

향후:

```text
Quality
├── Volume
├── Completeness
├── Validity
├── Uniqueness
└── Distribution
```

Public Status UI에서는 Quality 하나로 표현할 수 있다.

## Volume

<small>PRD §11.6 · #28</small>

질문:

> 데이터 양이 평소와 크게 달라졌는가?

### 두 종류의 Count — 섞지 않는다

<small>2026-10-01 관측(#28): `datago.air_quality` 응답 envelope 의 `totalCount=40`(서울
측정소 전체), 같은 응답의 실제 레코드는 `page_size` 만큼만 수신 — 두 값은 정의부터 다르다</small>

| 지표 | 뜻 | 의존 대상 |
|---|---|---|
| `provider_total_count` | 응답 envelope 의 `totalCount` — provider 가 선언하는 이 쿼리의 전체 결과 수 | Probe 설정과 무관, **쿼리에 의존** (같은 쿼리끼리만 비교) |
| `sample_count` | Watch 가 실제로 수신한 레코드 수 | Probe 설정(`page_size`)에 의존 |

규칙:

- 두 값은 **절대 하나의 baseline 에 섞지 않는다.** 각각 자신의 rolling baseline 을
  가진다.
- 이상 판정의 기본 신호는 `provider_total_count` 다 (있을 때). Provider 스스로
  밝힌 전체량이므로 페이지 잘림과 무관하다.
- `totalCount` 를 주지 않는 provider(odcloud 계열 등)는 `sample_count` 로 판정하되
  Evidence 에 그 사실을 명시한다 — "몇 개를 요청했고 몇 개를 받았는가"가 판정의
  일부가 된다.
- `sample_count` 가 요청한 `page_size` 보다 지속적으로 작은 것은 volume 이상이
  아니라 응답 잘림·빈 데이터의 별도 증상이다. 정보성일 수 있으므로 Health 를
  낮추지 않고 증상으로만 기록한다(D-008).
- `totalCount` 는 데이터의 자연스러운 증가(예: 이번 달 실거래 누적)도 반영한다.
  baseline 비교는 상대 변화율로 하고, 증가·감소 방향을 Evidence 에 남긴다.

### 판정 방식

```text
Recent baseline
9,800 ~ 10,400

Current
6,900

Deviation
-31%
```

MVP에서는 ML을 사용하지 않는다.

기본 방식:

```text
Rolling median
+
Dataset-specific threshold
```

예:

```yaml
volume:
  enabled: true

  metric: provider_total_count   # 기본값. totalCount 없는 provider 는 sample_count

  baseline:
    minimum_samples: 14
    window_size: 30

  warning:
    relative_change: 0.25

  critical:
    relative_change: 0.50
```

충분한 Baseline이 없는 경우:

```text
UNKNOWN
```

또는:

```text
Baseline building
```

으로 표시한다.

## Completeness

<small>PRD §11.7</small>

질문:

> 중요 Field의 값이 비정상적으로 사라지고 있는가?

예:

```text
Field
address

Normal null ratio
1.2%

Current
28.4%

Result
WARN
```

Dataset마다 관측할 Field를 Registry에 명시한다.

### 대상 Field 선정 기준

<small>#29 · 2026-10-01 관측 — Dataset마다 30건 샘플</small>

| 관측 | 채움율 | 대상 여부 |
|---|---|---|
| `tour_kor_area` · `title`·`addr1`·`zipcode`·`modifiedtime` | 30/30 채움 | 선정 |
| `tour_kor_area` · `firstimage` (3/30 비움), `hospital_info` · `hospUrl` (2/30) | 대부분 채움 | 선정 |
| `tour_kor_area` · `addr2` (26/30 비움), `tel` (29/30) | 대부분 비움 | 제외 |
| `localdata.general_restaurant` · `TELNO` (30/30 비움) | 항상 비움 | 제외 |
| `air_quality` · `pm25Flag` (29/30 비움) | 플래그 성격(이상 시에만 값) | 제외 |

규칙:

1. **등록 전 측정으로 고른다.** 후보 Field 는 Registry 등록 전 샘플 관측(예: 30건)으로
   채움율을 잰다. 기준: 이용 가치가 있는 Field(식별·위치·대표값·시간) 중 채움율이
   높은 것. 그 측정 결과가 선정 근거가 되므로 Registry 의 필드 선정도 근거 기반이다.
2. **상시 비어있는 Field 는 대상이 아니다.** 항상 비어 있으면(예: `TELNO` 30/30,
   `addr2` 87%) 이상을 감지할 신호가 없다. 이런 Field 는 관찰 대상에서 빼고,
   나중에 채워지기 시작하면 그 자체가 정보성 Change 다.
3. **Dataset 당 1~3개.** 모든 Field 를 무조건 분석하지 않는다(PRD 원칙).
4. **빈 값 표현을 하나로 본다.** JSON `null`·빈 문자열·`-`·`N/A` 를 "값 없음"으로
   정규화하되, 어떤 표현이었는지 Evidence 에 남긴다 — 실측에서 `air_quality` 는
   `khaiValue` 에 `-`, `pm25Flag` 에 JSON `null` 이 섞여 있었다.
5. **필드 자체가 사라지는 것은 Completeness 가 아니다.** 스키마에서 필드가 없어지는
   경우는 Contract Check 의 영역이다. Completeness 는 "필드는 있으나 값이 비어
   있는가"만 본다. 두 Check 의 결과는 함께 해석한다.

### 설정 예

```yaml
completeness:
  enabled: true

  fields:
    - address
    - modified_at
```

모든 Field를 무조건 분석하지 않는다.
