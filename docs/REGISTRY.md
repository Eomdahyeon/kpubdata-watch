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
    field: modifiedtime
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
