# 테스트 전략과 CI 게이트

> 이 문서는 KPubData Watch MVP PRD(v1.0 Draft, 2026-09-30)의 §70, §71, §72, §73, §74, §75 를 목적별로 나눈 것이다. 전체 대응표는 [문서 안내](index.md#prd) 에 있다.

## Test Strategy

<small>PRD §70</small>

### Unit Tests

```text
Availability Detector

Freshness Detector

Contract Detector

Volume Detector

Completeness Detector

Health Aggregator

Change Classification

Incident Lifecycle

Secret Redaction
```

## Fixture Regression Tests

<small>PRD §71</small>

예:

```text
tests/fixtures/

availability/
  healthy.json
  timeout.json
  500.json
  credential-error.json

contract/
  baseline.json
  field-added.json
  field-removed.json
  type-changed.json

freshness/
  fresh.json
  delayed.json

quality/
  normal-volume.json
  low-volume.json
  high-null.json
```

## Replay Tests

<small>PRD §72</small>

실제 변경 사례를 Fixture로 보존한다.

예:

```text
Historical API response BEFORE

Historical API response AFTER

Expected Detection
```

이를 통해 실제 변화 사례를 Regression Test로 재생한다.

Watch의 장기적인 경쟁력 중 하나가 된다.

## Integration Tests

<small>PRD §73</small>

Mock HTTP Server를 통해 전체 Pipeline을 검증한다.

```text
Probe
  ↓
Normalize
  ↓
Observation
  ↓
Detection
  ↓
Change
  ↓
Incident
  ↓
Health
```

## Live Tests

<small>PRD §74</small>

실제 API Credential이 있는 환경에서만 실행한다.

```bash
pytest -m live
```

일반 PR CI에서는 실행하지 않는다.

Scheduled CI 또는 수동 Smoke Test에서 사용한다.

## CI Quality Gates

<small>PRD §75</small>

기본:

```text
pytest

ruff

mypy

migration check

secret scan

dependency vulnerability scan
```

Live API 결과 자체 때문에 PR CI가 불안정해지지 않게 한다.

## 이 저장소의 CI 게이트 (현재)

`CI gate` 하나가 필수 체크이며 다음 잡을 모두 통과해야 한다 (`.github/workflows/ci.yml`).

| 잡 | 내용 |
|---|---|
| Lint & Type Check | ruff check · ruff format --check · 한국어 주석 게이트 · mypy strict · README parity · independence (Builder/Studio 의존 금지) |
| Test | pytest, Python 3.12 · 3.13 (`live` 마커 제외). `tests/unit/scripts/test_check_brand_tokens.py` 가 Brand v2 토큰 게이트(`scripts/check_brand_tokens.py`, [시각 정체성](VISUAL_IDENTITY.md) §8)를 이 저장소에 대해 실행한다 |
| Coverage Gate | `fail_under = 90` (`pyproject.toml`) |
| Build Package · Base install | sdist/wheel 빌드, extras 없이 설치 후 import·CLI |
| Docs Build | `mkdocs build --strict` |
| Secret scan | gitleaks 전체 이력 |

Security 워크플로(pip-audit · CodeQL)는 시리즈와 같이 병합을 막지 않는다. PRD 의 "migration check" 는 Alembic 이 들어오는 #4 에서 추가한다.
