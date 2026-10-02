# KPubData Watch

**이 공공데이터를 지금 믿고 사용할 수 있는가?**

> 한국 공공데이터 API 를 지속적으로 관측하고, 현재 상태와 변경·이상 이력을 근거와 함께 공개하는
> Public Data Reliability 서비스입니다. KPubData 위에서 동작하며 KPubData Builder 에는 의존하지 않습니다.
>
> 관련 프로젝트:
>
> - [KPubData](https://github.com/yeongseon/kpubdata) — 한국 공공데이터 접근을 위한 독립 Python SDK. Watch 가 의존하는 유일한 제품
> - [KPubData Builder](https://github.com/yeongseon/kpubdata-builder) — KPubData 로 재현 가능한 데이터셋·테이블을 만드는 형제 제품
> - [KPubData Studio](https://github.com/yeongseon/kpubdata-studio) — KPubData Builder 의 시각적 작업 공간

[English](./README.en.md)

## 무엇을 해결하나

공공 API 는 요청이 성공해도 데이터가 건강하다는 뜻이 아닙니다. `HTTP 200` 이어도 데이터가 3일째
갱신되지 않았거나, 건수가 평소의 60% 로 줄었거나, 필드가 사라졌을 수 있습니다.

```text
HTTP 200  ≠  Data Healthy
```

KPubData Watch 는 가용성뿐 아니라 **Freshness · Contract · Quality** 까지 관측하고, 모든 판정에
Expected · Observed · Difference · Rule · Evidence · Timestamp 를 남깁니다. "AI 가 이상하다고
판단했습니다" 같은 결과는 내지 않습니다.

## 현재 상태

**MVP — Public Status (0~3개월) 준비 중.** 저장소 골격과 CI 가 있고, 구현은 아직 없습니다.
MVP 목표는 3개 이상 Provider 의 실제 공공 Dataset 10개를 지속 관측하는 것입니다.
구현 순서와 완료 조건은 [ROADMAP](docs/ROADMAP.md) 에 있습니다.

## 문서

데모: <https://yeongseon.github.io/kpubdata-watch/> — Public Status 화면을 고정
Fixture 데이터로 보여주는 정적 데모입니다. 실제 관측 결과가 아닙니다
([ADR 0012](docs/decisions/0012-pages-hosts-a-fixture-demo-not-the-service.md)).

문서 사이트: <https://yeongseon.github.io/kpubdata-watch/docs/>

| 문서 | 내용 |
|---|---|
| [PRD](docs/PRD.md) | 제품 정의·문제·원칙·목표·비목표·성공 지표 |
| [ROADMAP](docs/ROADMAP.md) | MVP 범위(P0/P1/유예), 구현 순서, 완료 조건, 이후 단계 |
| [DOMAIN_MODEL](docs/DOMAIN_MODEL.md) | Health · Check · Detection · Change · Incident |
| [Detectors](docs/detectors/README.md) | Availability · Freshness · Contract · Quality |
| [ARCHITECTURE](docs/architecture/README.md) | Probe · Observation · Scheduler · 저장·배포 |
| [REGISTRY](docs/REGISTRY.md) | Dataset Registry 형식과 Dataset 선정 기준 |
| [UI](docs/UI.md) | UI 전략 · UI Lab · Public Status 화면 원칙 |
| [TESTING](docs/TESTING.md) | 테스트 전략과 CI 게이트 |
| [결정 기록](docs/decisions/README.md) | ADR 과 PRD 결정 로그(D-001~D-020) 대응표 |
| [API_CONTRACT](API_CONTRACT.md) | Public Read API 와 운영자 CLI (초안) |
| [SECURITY](SECURITY.md) | 보안 신고, credential·redaction 요구사항 |
| [CONTRIBUTING](CONTRIBUTING.md) · [AGENTS](AGENTS.md) | 기여 방법과 에이전트 규칙 |

프로젝트 관리 규칙의 정본은 kpubdata 의
[POLICY.md](https://github.com/yeongseon/kpubdata/blob/main/docs/governance/POLICY.md) 입니다.

## 제품군

| Repository | Role |
|---|---|
| [kpubdata](https://github.com/yeongseon/kpubdata) | 공공데이터 수집·정규화 SDK — Watch 가 의존하는 유일한 제품 |
| [kpubdata-builder](https://github.com/yeongseon/kpubdata-builder) | 데이터셋 파이프라인과 배포 — Watch 의 형제 제품, 의존하지 않음 |
| [kpubdata-studio](https://github.com/yeongseon/kpubdata-studio) | Builder 의 화면과 작업 흐름 |
| **kpubdata-watch** | 공공데이터 신뢰성 관측과 Public Status — 이 저장소 |

## 라이선스

[MIT](LICENSE)
