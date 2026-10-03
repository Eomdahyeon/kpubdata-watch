# ADR 0012: GitHub Pages 는 고정 Fixture 기반 데모와 문서만 호스팅한다

## 상태

채택됨(Accepted) — 2026-10-02 (#78)

## 요약 (English summary)

> GitHub Pages hosts two static things for this repository: a fixture-based
> demo of the Public Status page at the root
> (`https://kpubdata-lab.github.io/kpubdata-watch/`), and the mkdocs
> documentation site at `/docs/`. The demo renders
> the snapshot in `demo/fixtures/` through the same Jinja template a future
> FastAPI route will reuse (`scripts/build_demo.py`), clearly labelled as
> fixed sample data, never a live observation. It calls no provider, opens no
> database connection and holds no credential. The production service stays
> exactly what docs/architecture/README.md already says: FastAPI (`watch-web`)
> + a scheduler/probe worker (`watch-worker`) + PostgreSQL. Pages cannot run
> that service — it serves static files only — so this ADR records that the
> gap is intentional, not a shortcut taken under time pressure.

## 문제

Pages 에 무엇을 올릴지가 두 번 바뀌었다. 처음에는 문서 사이트만 루트에
배포했다(`.github/workflows/docs.yml`, #76). 그런데 KPubData Studio 는 같은
Pages 자리에 **Mock 데이터로 동작하는 실제 앱 데모**를 루트에 두고 문서를
`/docs/` 로 내렸다(`kpubdata-studio/.github/workflows/deploy.yml`, "Deploy demo
+ docs"). Watch 도 같은 제품군 관례를 따라야 하는가, 따른다면 Watch 는 아직
구현이 없는데(`src/kpubdata_watch/web/` 가 placeholder 뿐이었다) 무엇을
"데모"로 보여줄 수 있는가가 문제였다.

잘못 답하면 두 가지 위험이 있다.

- Pages 에 실제 FastAPI 서비스를 올리려 하면: PostgreSQL 도 없고, Provider
  Credential 을 정적 호스팅에 둘 수도 없다 — SECURITY.md 가 금지하는
  일이다.
- 반대로 아무 데모도 없이 문서만 두면: 제품을 평가하려는 사람이 설치 없이
  볼 수 있는 화면이 하나도 없다.

## 결정

1. **Pages 는 두 정적 산출물만 호스팅한다.** 루트는
   `scripts/build_demo.py` 가 `demo/fixtures/` 의 snapshot 을
   `src/kpubdata_watch/web/templates/` 의 제품 화면(Overview, Datasets,
   Dataset·Incident·Change 상세, Incident·Change 목록, #88)으로 렌더링한 결과,
   `/docs/` 는 `mkdocs build --strict` 결과다. 둘 다
   `.github/workflows/deploy.yml` ("Deploy demo + docs") 한 Workflow 가
   `main` push 에서만 배포하고, Pull Request 에서는 build 만 한다(Studio
   #586 의 concurrency 수정을 그대로 가져왔다 — build 가 필수 체크인데
   공유 group 에서 취소되면 PR 이 영구히 BLOCKED 된다).
2. **데모는 Fixture 고정 데이터이고, 항상 그렇게 표시한다.** 페이지에
   "데모 — 고정된 예시 데이터이며 실제 관측 결과가 아닙니다" /
   "Demo — fixed sample data, not a live observation result" 배너가 항상
   보인다. Fixture 는 `docs/REGISTRY.md`·`docs/detectors/freshness.md` 에
   실제로 등장하는 Provider·Dataset 이름을 최대한 쓰되, Watch 가 실제로
   그 Dataset 들을 지금 관측하고 있다는 뜻은 아니다.
3. **데모는 Public Status 의 실제 Template 을 그대로 쓴다.** Fixture를
   만드는 대신 가짜 Mock 데이터 생성기를 새로 만들지 않는다 —
   `web/templates/public_status.html` 은 향후 FastAPI Route
   (`GET /`) 가 Read Model 을 넣어 그대로 재사용할 Template 이고,
   `demo/fixtures/` 의 snapshot 은 공개 Read Model
   (`kpubdata_watch.api.read_models.public`, #82) 모양을 그대로 따른다. 그래서 데모와 실제 서비스 UI 가 따로 벌어지지
   않는다.
4. **데모는 Provider 를 호출하지 않고 Credential 을 갖지 않는다.** 빌드는
   `demo/fixtures/*.json` 을 읽는 순수 함수이고, 네트워크 호출이 없다.
   Secret scan(gitleaks)·`check_independence.py` 등 기존 게이트가 그대로
   적용된다.
5. **Production 배포 Architecture 는 바뀌지 않는다.** Watch 는
   `docs/architecture/README.md` §Deployment 그대로 `watch-web`
   (FastAPI) + `watch-worker`(Scheduler/Probe) + PostgreSQL 로 배포한다.
   Pages 는 이 셋 중 어느 것도 대체하지 않는다 — 정적 파일만 서빙할 수
   있어서, 대체하는 선택지 자체가 없었다.

## 결과

- `README.md`·`README.en.md` 가 데모 링크를 추가하고, 문서 링크를
  `/kpubdata-watch/docs/` 로 갱신한다.
- 향후 `GET /` Route(ROADMAP #12 Minimal public status) 는 같은
  `public_status.html` 을 FastAPI 의 실제 Read Model 로 렌더링하면 된다 —
  Template 을 새로 만들 필요가 없다.
- Fixture 데이터가 실제 운영 데이터처럼 보이지 않도록, 배너 문구와
  `scripts/build_demo.py`·`tests/unit/scripts/test_build_demo.py` 가 항상
  함께 검증한다(배너 누락은 테스트 실패).
- Pages 저장소 Homepage 는 데모 URL
  (`https://kpubdata-lab.github.io/kpubdata-watch/`) 로 설정한다.
