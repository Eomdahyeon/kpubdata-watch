# ADR 0007: Provider 의 Rate Limit 과 이용조건은 Registry 에 선언하고 검증이 지킨다

## 상태

채택됨(Accepted) — 2026-10-01 (#27, PRD §105 Q-003)

## 요약 (English summary)

> Providers do not announce their rate limits or terms of use through the API:
> data.go.kr responses carry no quota headers or envelope fields, and kpubdata
> 0.8.0 models terms as a free-text `LicenseSpec.quota`. So Watch declares them
> in the version-controlled registry — machine-readable rate limits (scope,
> window, count, minimum interval) with a source URL and a verified date, and
> terms reusing kpubdata's `LicenseSpec` vocabulary — and the registry
> validation rejects a dataset set whose daily probe budget (interval plus
> confirmation-probe headroom) exceeds the declared limit. At runtime a
> `RateLimitError` overrides the declaration: Watch backs off, and its own
> throttling is never recorded as a provider outage.

## 문제

Watch 는 Dataset 마다 주기적으로 probe 한다. Provider 는 호출량 제한과 이용조건
(라이선스, 저작표시, 재배포 조건)을 부과한다. 관측(#27, 2026-10-01)에 따르면:

- data.go.kr 계열 응답에는 quota 를 알려주는 header 나 envelope 필드가 없다.
  kpubdata 0.8.0 의 HTTP transport 는 `Content-Type` 과 `Retry-After` 만 읽는다.
- kpubdata `LicenseSpec` 은 이용조건 모델(`redistribution`, `attribution`,
  `quota` 등)을 이미 갖고 있지만 `quota` 는 자유 문자열이고, provider catalogue
  (catalogue.json 150개 항목)에는 기계 판독 가능한 rate limit 필드가 없다
  (`license_note` 가 3개 항목에만 있다).
- 제한은 data.go.kr 에서 서비스(활용신청) 단위로, 사람이 각 서비스의 활용가이드
  페이지에서 읽어야 한다. 서로 다른 Dataset 이 같은 활용신청을 공유할 수 있다.

제한을 Registry 에 선언하지 않으면 Scheduler 는 예산을 모르고, 선언만 하고
검증이 없으면 임의의 `interval_minutes` 가 예산을 넘어도 아무도 알지 못한다.
규칙 없는 게이트는 소원일 뿐이다(POLICY 18.2).

## 결정

1. **Registry 에 provider 공유 섹션을 둔다.** Dataset 파일과 분리된
   `registry/providers.yaml` 에 provider 단위 정보를 버전 관리한다.
2. **Rate limit 은 기계 판독 숫자로 선언한다** — 적용 범위(`scope`), 창(`window`),
   횟수, 최소 호출 간격. 출처 URL 과 확인일(`verified_at`)을 반드시 함께 둔다.
   근거 없는 값은 `unknown` 이고, `unknown` 은 "제한 없음"이 아니다.
3. **이용조건은 kpubdata `LicenseSpec` 의 어휘를 그대로 쓴다** — `type`,
   `commercial_use`, `attribution_required`, `attribution`, `redistribution`,
   `modification_allowed`, `pii_columns`, `note`. Watch 가 두 번째 용어 체계를
   만들지 않는다(ADR 0004). Dataset 단위 라이선스가 다르면 Dataset 항목이
   provider 값을 덮어쓴다(override).
4. **Registry 검증이 예산을 계산해 거부한다.** 같은 `scope`(data.go.kr 은
   서비스 활용신청)를 공유하는 Dataset 들의 일일 probe 수 합
   (`1440 / interval_minutes`)에 실패 시 확인 probe 여유(기본 ×2)를 더한 값이
   선언된 일일 한도를 넘으면 registry 로딩이 실패한다. Interval 실수를 운영
   시점이 아니라 등록 시점에 잡는다.
5. **Runtime 은 선언을 신뢰하지 않는다.** kpubdata `RateLimitError` 를 관측하면
   해당 provider 의 예산을 즉시 낮추고(동적 백오프), 선언값과 실제의 차이를
   Change 가 아닌 운영 이벤트로 기록한다. Watch 자신의 호출이 원인이면 그것은
   provider 장애가 아니다(D-009 과 같은 원리).

## 결과

- Registry 형식은 [REGISTRY](../REGISTRY.md) 의 provider 예시를 따른다. 검증
  규칙은 Dataset Registry 구현 시 gate 테스트와 함께 구현한다.
- 이용조건의 `attribution` 텍스트는 Public Status 의 Dataset 상세에 그대로
  노출하고, `unknown` 항목은 운영자 화면에 "확인 필요" 로 표시한다.
- `terms_source.verified_at` 이 오래된 항목은 주기 점검 대상이며, 자동 갱신은
  하지 않는다(Official Notice 자동 수집 제외, D-018 과 같은 선).

## 예시

```yaml
# registry/providers.yaml
- id: datago
  rate_limits:
    - scope: service            # data.go.kr: 활용신청(서비스) 단위로 적용
      requests_per_day: 5000    # 값은 예시 — 활용가이드 문서에서 읽은 수만 쓴다
      min_interval_seconds: 2
  terms:                        # kpubdata LicenseSpec 어휘
    redistribution: allowed
    attribution_required: true
    attribution: "출처 표시 텍스트"
  terms_source:
    url: https://www.data.go.kr/data/15073861/openapi.do
    verified_at: 2026-10-01
```

```yaml
# registry/datasets/*.yaml — Dataset 단위 덮어쓰기 (해당 시)
id: visitkorea-tourism
provider: datago
terms:
  redistribution: non_commercial   # 이 Dataset 만 provider 와 다를 때
```
