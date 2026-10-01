# Freshness

> 이 문서는 KPubData Watch MVP PRD(v1.0 Draft, 2026-09-30)의 §11.2 를 목적별로 나눈 것이다. 전체 대응표는 [문서 안내](../index.md#prd) 에 있다.

## Freshness

<small>PRD §11.2</small>

질문:

> 데이터가 예정된 시점에 갱신되고 있는가?

Dataset Registry에 명시적으로 설정한다.

예:

```yaml
freshness:
  enabled: true
  field: modified_at

  timezone: Asia/Seoul

  expected_interval: 24h
  grace_period: 2h
```

예:

```text
Expected
Daily update

Latest data
2026-09-30 05:58 KST

Current time
2026-09-30 07:10 KST

Result
PASS
```

또는:

```text
Expected
06:00 ± 1h

Latest data
Previous day 06:04

Result
WARN

Freshness delayed
```

Freshness는 공공데이터 특화 기능 중 핵심으로 취급한다.

## 관측 근거 — Dataset별 Freshness 필드

<small>#26 실측, 2026-10-01 — kpubdata 0.8.0 로 data.go.kr 계열 Dataset 을 각 1~3 건 조회</small>

Freshness Check 는 Registry 의 `field` 하나가 아니라, 아래 세 종류의 시간 필드를
추출 대상으로 삼아야 한다. 관측된 값은 모두 KST naive 시간이었다 — Registry 의
`timezone: Asia/Seoul` 가정이 유지된다.

| 종류 | 의미 | 관측된 Dataset · 필드 (표본값) |
|---|---|---|
| Record 수정 시각 | 레코드가 provider 에서 마지막으로 수정·갱신된 시각 | `datago.tour_kor_area` · `modifiedtime` (`20250707103442`), `localdata.general_restaurant` · `DAT_UPDT_PNT` (`2026-09-30 22:47:51`), `LAST_MDFCN_PNT` (`2026-09-29 12:01:13`) |
| 관측 시각 | 실시간 관측값의 측정 시각 | `datago.air_quality` · `dataTime` (`2026-10-01 20:00`), `datago.airkorea_station_realtime` · `dataTime` |
| 사건 시각 (조합) | 레코드의 사건 발생 시각이 연·월·일 필드로 쪼개져 있음 | `datago.apt_trade` · `dealYear/dealMonth/dealDay` (`2026-09-23`), `datago.apt_rent` · 동일 |

그 밖의 관측:

- `datago.social_enterprise` · `baseD` (`2025-11-04`) 는 레코드별 수정 시각이
  아니라 데이터 전체의 기준일이다. Freshness 신호로 쓸 수 있지만 Dataset 단위
  신호이며, 별도 종류로 다룬다.
- `datago.hospital_info` 는 시간 필드로 `estbDd`(설립일)만 가진다 — Freshness 를
  레코드에서 추출할 수 없는 Dataset 이 실제로 존재한다.
- 기상청 단기예보 3종(초단기실황·초단기예보·동네예보)은 이 관측 호스트에서
  `APPLICATION_ERROR` 로 호출 자체가 되지 않았다(해외 IP 차단으로 추정). 두
  번에 걸쳐 재시도해도 같았다. `baseDate/baseTime` 필드의 존재는 문서상으로만
  알려져 있고 이 관측에서는 확인되지 않았다.
- 관측에 쓴 Service Key 는 data.go.kr 의 일부 서비스만 활성화되어 있다(403 다수).
  위 표는 활성화된 서비스에 대한 실측이지, data.go.kr 전체가 아니다.
