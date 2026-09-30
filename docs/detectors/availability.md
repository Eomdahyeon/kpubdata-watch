# Availability

> 이 문서는 KPubData Watch MVP PRD(v1.0 Draft, 2026-09-30)의 §11.1 를 목적별로 나눈 것이다. 전체 대응표는 [문서 안내](../index.md#prd) 에 있다.

## Availability

<small>PRD §11.1</small>

질문:

> API에 정상적으로 접근할 수 있는가?

관측 대상:

```text
DNS
TCP Connection
TLS
Timeout
HTTP Status
Provider-defined Error
Response Parse
```

예:

```text
PASS
HTTP 200
Provider response valid
```

```text
FAIL
HTTP 503
```

```text
FAIL
Timeout after 15s
```

Credential 문제는 별도 분류한다.

```text
401 / 403

Provider problem?
        vs
Watch credential problem?
```

Watch가 사용하는 API Key의 문제로 판단되는 경우:

```text
Check = UNKNOWN
Monitoring Error
```

로 처리하고 Provider Outage로 표시하지 않는다.
