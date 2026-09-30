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

<small>PRD §11.6</small>

질문:

> 데이터 양이 평소와 크게 달라졌는가?

예:

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

예:

```yaml
completeness:
  enabled: true

  fields:
    - address
    - modified_at
```

모든 Field를 무조건 분석하지 않는다.
