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
   단, kpubdata 가 `LicenseSpec.pii_columns` 로 선언한 Field 는 채움율과 무관하게
   **선정하지 않는다.** Completeness Evidence 는 값의 원표현(규칙 4)을 남기는데,
   개인정보는 저장하지 않는다는 결정(ADR 0006 D-017)과 부딪치기 때문이다. 어휘는
   kpubdata 의 것을 그대로 쓴다(ADR 0007). 예: kpubdata 의
   `localdata.general_restaurant` 는 `TELNO` 를 `pii_columns` 로 선언한다 — 위 표에서
   이미 "항상 비움"으로 제외됐지만, 채워지기 시작해도 대상이 되지 않는다.
2. **상시 비어있는 Field 는 대상이 아니다.** 항상 비어 있으면(예: `TELNO` 30/30,
   `addr2` 87%) 이상을 감지할 신호가 없다. 이런 Field 는 관찰 대상에서 빼고,
   나중에 채워지기 시작하면 그 자체가 정보성 Change 다.
3. **Dataset 당 1~3개.** 모든 Field 를 무조건 분석하지 않는다(PRD 원칙).
4. **빈 값 표현은 Field 타입에 따라 정규화한다.** 타입은 kpubdata 가 선언한
   `FieldSpec.type` 이고, 어떤 표현이었는지는 Evidence 에 남긴다.
   - **숫자 Field**(`integer`·`number`): kpubdata 와 같게, 앞뒤 공백을 지운 뒤
     `""`·`-` 를 JSON `null` 과 함께 "값 없음"으로 본다. kpubdata 의
     `_DEFAULT_NULL_MARKERS = frozenset({"", "-"})` 와 그 null 집계가 이 범위다
     (kpubdata#615). 실측에서 `air_quality` 의 `khaiValue`(kpubdata 선언
     `integer`) 에 `-` 가 있었다.
   - **문자열 Field**(그 밖의 타입·미선언 Field): JSON `null` 과 빈 문자열(공백만
     있는 문자열 포함)만 "값 없음"이다. `-` 는 문자열에서 의미 있는 값일 수 있으므로
     값으로 센다 — kpubdata 가 null 인식을 숫자 casting 으로 한정한 이유와 같다.
     빈 문자열을 "값 없음"으로 보는 것은 kpubdata 의 validation 집계(문자열 Field 는
     원값을 그대로 non-null 로 센다)보다 넓다. Completeness 의 질문은 "값이
     비어 있는가"이고, 빈 문자열은 표현만 다를 뿐 값이 없기 때문이다. 어떤 문자열
     Field 에서 `-` 가 결측 표기임이 실측으로 확인되면, 그 Field 에 한해 Registry 에
     근거와 함께 선언한다 — 전역 규칙으로 넓히지 않는다.
   - 실측(#29)에서 확인된 표현은 숫자 Field 의 `-`(`khaiValue`)와 JSON
     `null`(`pm25Flag`)뿐이다. `N/A` 같은 다른 표기는 실측 근거가 없으므로 규칙에
     넣지 않는다 — 관측되면 근거와 함께 추가한다.
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
