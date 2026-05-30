# CLAUDE.md — 프로젝트 컨텍스트

이 파일은 Claude Code 또는 Antigravity 등 에이전트들이 매 세션 시작 시 자동으로 로드하여 읽는 진입점 파일입니다.
프로젝트 규칙은 `AGENTS.md`에, 아키텍처는 `docs/decisions.md`에 있습니다.
이 파일은 **현재 상태**와 **세션 간 연속성**에 집중합니다.

## 프로젝트 현황 (2026-05-31)

기상청(KMA) 공공데이터포털(`VilageFcstInfoService_2.0`)과 APIHub를 Python에서 편하게 사용하기 위한 공용 클라이언트 라이브러리(`kma`).
현재 동기/비동기 통합 호출(`httpx` 기반) 및 `LatLon`/`GridPoint`/mapping 좌표 변환, 발표시각 자동 계산, Pydantic v2 frozen 모델을 기반으로 안정적인 public surface를 제공합니다. 또한 data.go.kr 86개 dataset 카탈로그 및 20개 이상의 helper, APIHub 470개 generated wrapper가 완비되어 있고 100개가 넘는 견고한 mock 테스트 게이트를 지니고 있습니다.

### 현재 작업

- maplibre-vworld-js 프로젝트의 뛰어난 에이전트 개발 스타일, 고정 worktree 정책, AI용 가이드 문서, 그리고 MCP 설정을 가져와서 본 프로젝트에 적합하게 적용 중입니다 (`feat/style-and-mcp-settings` 브랜치).

### 잔존 기술 부채

- `docs/resume.md`의 백로그를 참고합니다. 주요 부채는 HTTP 에러 핸들링 공통화 및 result code 예외 처리 통합입니다.

## 에이전트 worktree + CodeGraph

ChatGPT Codex는 `F:\dev\python-kma-api-codex`, Claude Code는 `F:\dev\python-kma-api-claude`, Google Antigravity 2.0은 `F:\dev\python-kma-api-antigravity`를 고정 worktree로 사용합니다. 새 작업은 해당 worktree에서 `git fetch` 후 `git switch -c agent/<topic> main`으로 브랜치를 생성하여 작업합니다. CodeGraph는 worktree마다 1회 `codegraph init -i`로 초기화하고 이후에는 `codegraph sync`를 통해 상태를 유지합니다. `.codegraph/`는 gitignore 대상입니다.

## 로컬 개발 환경

```text
f:\dev\python-kma-api\
├── src/kma/          # 패키지 소스 코드
│   ├── client.py     # KmaClient 타입화 단기예보 클라이언트
│   ├── datagokr.py   # DataGoKrClient data.go.kr 범용 클라이언트
│   ├── apihub.py     # ApiHubClient APIHub 범용 클라이언트
│   ├── grid.py       # LCC DFS 좌표 변환 식
│   ├── models.py     # Pydantic 응답 모델
│   └── ...
├── tests/            # pytest 단위 테스트 스위트
├── tools/            # Streamlit 디버그 UI 등
└── docs/             # 아키텍처 ADR, journal, tasks 문서들
```

Python 3.10 이상. 가상환경(`.venv`) 활성화 후 `pip install -e ".[dev]"`로 셋업합니다.

## 빠른 검증 명령

```bash
# 의존성 설치
pip install -e ".[dev]"

# 품질 게이트 (PR 전 로컬에서 반드시 실행)
python -m pytest -q
python -m ruff check .
python -m mypy src/kma
codegraph sync && codegraph status
```

## 주요 결정 사항 (ADR 요약)

- **ADR-001: httpx 기반 HTTP 클라이언트**: 동기/비동기 호출의 일관성과 `params=` 인코딩 최적화를 위함.
- **ADR-002: Pydantic v2 frozen 모델**: 응답 모델의 불변성과 비교/직렬화의 예측 가능성을 보장.
- **ADR-003: 인증값 보안 정책**: 로그, 캐시 키, Pydantic repr에 `serviceKey` / `authKey` 유출 원천 차단.
- **ADR-004: data.go.kr/APIHub 이중 gateway 분리**: 인증 방식 및 동작이 다른 두 gateway의 결합도 최소화.

## 작업 후 의무사항

1. `docs/journal.md`에 항목 추가 (날짜·요약·관련 파일·결정·다음 작업, 역시간순)
2. `docs/resume.md`의 진척도 및 다음 작업 업데이트
3. 결정 변경이 있었다면 `docs/decisions.md`에 ADR 추가
4. 사용자 가시 변경이면 `CHANGELOG.md` 갱신
5. `pytest`, `ruff`, `mypy` 검증 무사 통과 확인
