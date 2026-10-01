# Dataset Registry

> 이 문서는 KPubData Watch MVP PRD(v1.0 Draft, 2026-09-30)의 §13, §68, §69 를 목적별로 나눈 것이다. 전체 대응표는 [문서 안내](index.md#prd) 에 있다.

## Dataset Registry

<small>PRD §13</small>

모든 관측 설정은 Version-controlled Registry에서 관리한다.

초기에는 Admin UI를 만들지 않는다.

예:

```yaml
id: visitkorea-tourism
provider: visitkorea

display_name: 한국관광공사 관광정보

category:
  - tourism

enabled: true

probe:
  operation: area_based_list

  params:
    area_code: "1"
    page_no: 1
    num_of_rows: 100

schedule:
  interval_minutes: 60

request:
  timeout_seconds: 15
  max_response_bytes: 2000000

checks:

  availability:
    enabled: true

  freshness:
    enabled: true
    kind: record_modified
    fields: [modifiedtime]
    format: "%Y%m%d%H%M%S"
    timezone: Asia/Seoul
    expected_interval: 24h
    grace_period: 2h

  contract:
    enabled: true

  quality:

    volume:
      enabled: true
      metric: total_record_count   # totalCount 없는 provider 는 record_count
      minimum_samples: 14

    completeness:
      enabled: true
      fields:
        - addr1

```

## Freshness 설정 — 추출 종류

<small>#54 · [Freshness 관측 근거](detectors/freshness.md#dataset-freshness) (#26)</small>

Freshness 신호는 Dataset 마다 모양이 다르다. 필드 하나(`field: modified_at`)로는
여러 필드를 조합하는 사건 시각, 형식이 다른 문자열, Dataset 단위 기준일, 추출할
수 없는 Dataset 을 표현할 수 없으므로, `freshness` 는 **추출 종류(`kind`)** 와 그에
필요한 필드·형식·시간대를 선언한다.

| 키 | 뜻 |
|---|---|
| `kind` | `record_modified` · `observed_at` · `event_date_parts` · `dataset_reference_date` 중 하나 |
| `fields` | 값을 읽을 필드 목록. `event_date_parts` 는 연·월·일 순서의 필드들이고, 나머지는 필드 하나 |
| `format` | 값을 해석할 `strptime` 형식. 값은 kpubdata 가 정규화한 뒤의 값을 문자열로 바꿔 읽는다 — kpubdata 가 `integer` 로 casting 한 필드(예: `modifiedtime`, `dealYear`)도 그 십진 문자열에 형식을 적용한다. `event_date_parts` 는 필드 값을 `-` 로 이어 붙인 문자열에 적용한다 |
| `timezone` | 시간대 정보가 없는 값을 해석할 IANA 시간대. 관측된 값은 모두 KST naive 였다(#26). 생략할 수 없다 |
| `enabled: false` + `reason` | 레코드에서 Freshness 를 뽑을 수 없는 Dataset. Check 결과는 `NOT_APPLICABLE` 이고 `reason` 은 생략할 수 없다 |

| `kind` | 의미 | 한 응답에서 고르는 값 |
|---|---|---|
| `record_modified` | 레코드가 provider 에서 마지막으로 수정·갱신된 시각 | 수신한 레코드 중 가장 늦은 시각 |
| `observed_at` | 실시간 관측값의 측정 시각 | 수신한 레코드 중 가장 늦은 시각 |
| `event_date_parts` | 연·월·일 필드로 쪼개진 사건 발생 시각 | 조합한 날짜 중 가장 늦은 날짜 |
| `dataset_reference_date` | 레코드별이 아닌 데이터 전체의 기준일 | 수신한 레코드 중 가장 늦은 기준일 |

고른 값이 Observation 의 `latest_data_at` 이 된다. 날짜만 있는 형식(`%Y-%m-%d`)은
그 날 00:00(`timezone`)으로 해석하므로, `expected_interval`·`grace_period` 는 하루
해상도를 고려해 정한다.

[Freshness 관측 근거](detectors/freshness.md#dataset-freshness)의 표와 1:1 로 대응하는
예 (값의 모양은 #26 실측 표본값):

```yaml
# Record 수정 시각 — datago.tour_kor_area · modifiedtime (20250707103442)
freshness:
  enabled: true
  kind: record_modified
  fields: [modifiedtime]
  format: "%Y%m%d%H%M%S"
  timezone: Asia/Seoul
  expected_interval: 24h
  grace_period: 2h
```

```yaml
# Record 수정 시각 — localdata.general_restaurant · DAT_UPDT_PNT (2026-09-30 22:47:51)
# 같은 형식의 LAST_MDFCN_PNT (2026-09-29 12:01:13) 도 후보다 — 어느 쪽을 읽을지는 등록 때 정한다
freshness:
  enabled: true
  kind: record_modified
  fields: [DAT_UPDT_PNT]
  format: "%Y-%m-%d %H:%M:%S"
  timezone: Asia/Seoul
  expected_interval: 24h
  grace_period: 2h
```

```yaml
# 관측 시각 — datago.air_quality · dataTime (2026-10-01 20:00)
# datago.airkorea_station_realtime 도 같은 dataTime
freshness:
  enabled: true
  kind: observed_at
  fields: [dataTime]
  format: "%Y-%m-%d %H:%M"
  timezone: Asia/Seoul
  expected_interval: 1h
  grace_period: 1h
```

```yaml
# 사건 시각(조합) — datago.apt_trade · dealYear/dealMonth/dealDay (2026-09-23)
# datago.apt_rent 도 같은 세 필드
freshness:
  enabled: true
  kind: event_date_parts
  fields: [dealYear, dealMonth, dealDay]
  format: "%Y-%m-%d"
  timezone: Asia/Seoul
  expected_interval: 168h
  grace_period: 24h
```

```yaml
# Dataset 단위 기준일 — datago.social_enterprise · baseD (2025-11-04)
freshness:
  enabled: true
  kind: dataset_reference_date
  fields: [baseD]
  format: "%Y-%m-%d"
  timezone: Asia/Seoul
  expected_interval: 8760h
  grace_period: 720h
```

```yaml
# 추출 불가 — datago.hospital_info (시간 필드는 estbDd 설립일뿐)
freshness:
  enabled: false
  reason: 레코드의 시간 필드가 설립일(estbDd)뿐이라 갱신 시각을 뽑을 수 없다 (#26)
```

`expected_interval`·`grace_period` 값은 예시다. 갱신 주기는 Dataset 등록 때
provider 문서와 관측으로 정한다 — 위 값은 실측된 주기가 아니다.

검증 (Registry 로딩 시, 구현은 Epic 2):

- `kind` 가 네 값 중 하나가 아니면 로딩이 실패한다.
- `fields` 의 개수가 `kind` 와 맞지 않으면 실패한다 — `event_date_parts` 는 셋,
  나머지는 하나.
- `format` 이 `strptime` 형식으로 해석되지 않거나 날짜 지시자(`%Y`·`%m`·`%d`)가
  빠져 있으면 실패한다. `timezone` 이 IANA 시간대가 아니면 실패한다.
- `enabled: false` 에 `reason` 이 없으면 실패한다. `enabled: true` 에 `kind`·
  `fields`·`format`·`timezone` 중 하나라도 없으면 실패한다.
- 실행 중 값이 `format` 과 맞지 않으면 그 관측의 Freshness 는 `UNKNOWN` 이고
  Evidence 에 원래 값과 형식을 남긴다 — 오래된 데이터(`FAIL`)로 판정하지 않는다.
- 이 규칙들은 종류별 파서와 함께 실측 값으로 된 fixture 테스트를 갖는다
  ([테스트](TESTING.md)).

## Provider 선언 — Rate Limit 과 이용조건

<small>#27 · [ADR 0007](decisions/0007-registry-declares-provider-rate-limits-and-terms.md)</small>

Provider 가 공유하는 정보는 Dataset 파일과 분리된 `registry/providers.yaml` 에
버전 관리한다. Provider 는 API 로 quota 를 알려주지 않으므로(응답 header ·
envelope 에 없음 — 2026-10-01 관측), 사람이 활용가이드에서 읽은 값을 출처와
확인일과 함께 선언한다.

```yaml
- id: datago
  rate_limits:
    - scope: service            # data.go.kr: 활용신청(서비스) 단위 적용
      requests_per_day: 5000    # 값은 예시 — 문서에서 읽은 수만 쓴다
      min_interval_seconds: 2

  terms:                        # kpubdata LicenseSpec 어휘를 그대로 쓴다
    redistribution: allowed
    attribution_required: true
    attribution: 출처 표시 텍스트

  terms_source:
    url: https://www.data.go.kr/data/15073861/openapi.do
    verified_at: 2026-10-01
```

- **검증이 예산을 지킨다.** 같은 `scope` 를 공유하는 Dataset 들의 일일 probe 수
  합계(`1440 / interval_minutes`)에 확인 probe 여유(기본 ×2)를 더한 값이
  `requests_per_day` 를 넘으면 registry 로딩이 실패한다.
- **근거 없는 값은 `unknown`** 이고 "제한 없음"이 아니다. `terms_source` 는
  생략할 수 없다.
- **Runtime 은 선언을 신뢰하지 않는다.** `RateLimitError` 관측 시 해당 provider
  예산을 즉시 낮추고(동적 백오프), Watch 스스로 제한에 걸린 것은 provider 장애로
  기록하지 않는다.
- Dataset 마다 라이선스가 다르면 Dataset 항목의 `terms:` 가 provider 값을
  덮어쓴다.

## Dataset Selection

<small>PRD §68</small>

첫 10 Dataset은 유명도만으로 선택하지 않는다.

평가기준:

```text
KPubData에서 안정적으로 호출 가능

명확한 Schema

합리적인 API 호출 제한

지속 관측 가능

갱신주기 확인 가능

실제 활용도가 있음

여러 Provider를 포함

다양한 변화 시나리오를 검증 가능
```

## Initial Dataset Portfolio

<small>PRD §69</small>

가능하면 다음 조합을 구성한다.

```text
2
Realtime / Near-realtime

4
Daily

2
Weekly / Monthly

2
Known contract/change history
```

Format도 다양하게:

```text
JSON
XML
```

Provider도:

```text
≥ 3
```

를 목표로 한다.
