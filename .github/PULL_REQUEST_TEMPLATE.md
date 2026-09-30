<!--
PR 제목은 Conventional Commits 형식이어야 합니다 — `PR title` 체크가 검사합니다 (kpubdata POLICY 2.1.3).
type: feat fix docs test perf refactor ci build chore style revert
이슈 번호는 제목이 아니라 본문에 적습니다 (Closes #123). squash 병합이 PR 번호를 붙입니다.
예) feat(detectors): classify removed response fields as breaking
-->

## 요약
<!-- 이 PR이 무엇을, 왜 바꾸는지 1~3문장으로 설명하세요. -->

## 변경 내용
<!-- 주요 변경 사항을 항목으로 나열하세요. -->
-

## 관련 이슈
<!-- 예) Closes #123, Refs #456 -->

## 검증
<!-- 어떻게 검증했는지 구체적으로 적으세요. -->
- [ ] Ruff lint / format 통과
- [ ] mypy 타입 체크 통과
- [ ] 테스트 통과 (`pytest`)
- [ ] 새 Detector 는 판단 근거(Expected·Observed·Difference·Rule·Evidence·Timestamp)를 남기고, fixture 회귀 테스트를 포함 (해당 시)
- [ ] 문서 변경 시 docs strict 빌드 통과 (해당 시)

## 체크리스트
- [ ] 기능 브랜치에서 작업했으며 `main`에 직접 push하지 않았다
- [ ] 커밋 메시지를 영어로 작성했다
- [ ] 로그·DB·API·HTML 어디에도 credential 이 남지 않는다 (SECURITY.md)
- [ ] 사용자 노출 변경 시 문서를 분류해 갱신했다: 제품→docs/PRD.md, 향후 의도→docs/ROADMAP.md, 릴리스 변경→CHANGELOG (해당 시)
