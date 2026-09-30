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
      minimum_samples: 14

    completeness:
      enabled: true
      fields:
        - addr1

```

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
