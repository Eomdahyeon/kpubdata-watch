# ADR 0004: KPubData Watch 는 KPubData 에만 의존하고 Builder 에는 의존하지 않는다

## 상태

채택됨(Accepted) — 2026-09-30 (PRD v1.0 Draft 결정 로그 D-016)

## 요약 (English summary)

> Watch may depend on KPubData and on nothing else in the family. It never imports
> or declares KPubData Builder or KPubData Studio. Builder and Watch are sibling
> products; any interoperation later goes through a manifest, an artifact or a
> protocol, not a dependency. `scripts/check_independence.py` enforces this in CI.

## 문제

KPubData 제품군의 의존성 방향은 `Studio → Builder → KPubData` 다 (kpubdata ADR 0007).
Watch 는 Builder 가 만든 산출물이 아니라 공공 API 자체를 관측하므로, Builder 에 의존하면
관측 대상과 무관한 파이프라인의 변경·릴리스에 묶이게 된다.

```text
허용                     허용하지 않음
kpubdata-watch           kpubdata-watch
      ↓                        ↓
   kpubdata              kpubdata-builder
```

## 결정

- **D-016** KPubData Watch 는 KPubData 에 의존할 수 있지만 Builder 에는 의존하지 않는다.
  Studio 에도 의존하지 않는다.
- Watch 는 KPubData 의 공개 API 만 사용한다 (kpubdata ADR 0007 과 같은 원칙).
- Builder 와 Watch 는 sibling product 로 유지한다. 필요한 상호운용은 향후 Manifest / Artifact /
  Protocol 로 처리한다.

## 결과

- `scripts/check_independence.py` 가 `kpubdata_builder`·`kpubdata_studio` import 와
  `pyproject.toml` 의 의존성 선언을 CI 에서 실패시킨다. 테스트가 위반을 심어 실패를 확인한다.
- kpubdata 의 제품군 문서(ADR 0007, README, TERMINOLOGY)에 Watch 를 추가하는 일은 kpubdata
  저장소의 이슈로 다룬다.
