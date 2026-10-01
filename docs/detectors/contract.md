# Contract

> 이 문서는 KPubData Watch MVP PRD(v1.0 Draft, 2026-09-30)의 §11.3, §11.4 를 목적별로 나눈 것이다. 전체 대응표는 [문서 안내](../index.md#prd) 에 있다.

## Contract

<small>PRD §11.3</small>

기존의 `Schema`보다 넓은 개념으로 `Contract`를 사용한다.

공공 API Contract에는 다음이 포함될 수 있다.

```text
Endpoint
Request Parameter
Response Structure
Field
Field Type
Pagination
Error Format
```

MVP 자동 탐지 범위:

```text
Response field added
Response field removed
Field type changed
Nested structure changed
Expected request contract failure
Provider-specific contract error
```

MVP에서 자동으로 해결하지 않는 것:

```text
문서만 바뀌었지만 API는 아직 동일한 경우 자동 발견
Endpoint migration 자동 추론
Renamed parameter 자동 migration 생성
```

이 부분은 Official Notice / 향후 Explain 기능과 결합한다.

## Contract Change Classification

<small>PRD §11.4</small>

### Additive

예:

```text
+ manufacturerName: string
```

기본:

```text
Change = INFO
Health impact = none
```

---

### Potentially Breaking

예:

```text
nullable → non-nullable
```

Dataset별 정책에 따라:

```text
WARNING
```

---

### Breaking

예:

```text
- addr2

price:
integer → string
```

기본:

```text
Incident
Severity = CRITICAL
```

<small>[ADR 0008](../decisions/0008-breaking-contract-default-severity.md) (#30) —
세 가지 경계와 함께 확정:</small>

- Incident 는 **확인 probe 후** 개시한다. 첫 탐지는 Change(Breaking 분류)로 기록한다.
- Diff 의 기준은 **마지막으로 확인된 스냅샷**이다. 실패·빈·잘린 응답은 Contract diff
  를 만들지 않고 Availability/Quality 신호가 된다.
- Dataset 별 override 로 **WARNING 까지만** 낮출 수 있다(사람만 하며, Breaking 이
  INFO 가 되는 경우는 없다).
