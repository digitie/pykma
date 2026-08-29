# CLAUDE.md — 프로젝트 컨텍스트

이 파일은 Claude Code 또는 Antigravity 등 에이전트들이 매 세션 시작 시 자동으로 로드하여 읽는 진입점 파일입니다.
프로젝트 규칙은 `AGENTS.md`에, 아키텍처는 `docs/decisions.md`에 있습니다.
이 파일은 **현재 상태**와 **세션 간 연속성**에 집중합니다.

## 프로젝트 개요

기상청(KMA) 공공데이터포털(`VilageFcstInfoService_2.0`)과 APIHub를 Python에서 편하게 사용하기 위한 공용 클라이언트 라이브러리(`kma`).
동기/비동기 통합 호출(`httpx` 기반) 및 `LatLon`/`GridPoint`/mapping 좌표 변환, 발표시각 자동 계산, Pydantic v2 frozen 모델을 기반으로 안정적인 public surface를 제공합니다. 또한 data.go.kr 86개 dataset 카탈로그 및 20개 이상의 helper, APIHub 470개 generated wrapper가 완비되어 있고 100개가 넘는 견고한 mock 테스트 게이트를 지니고 있습니다.

현재 진척도와 다음 작업은 `docs/resume.md`, 최근 작업 이력은 `docs/journal.md`, 남은 백로그는 `docs/tasks.md`를 참고하세요. 이 파일에 진척도를 하드코딩하지 않습니다 — 오래된 상태 정보가 남는 것을 막기 위함입니다.

## 에이전트 worktree

에이전트별 고정 worktree 경로와 CodeGraph 초기화 절차는 `AGENTS.md`의 "개발 환경 및 에이전트 정책"을 따릅니다. 여기서 중복 서술하지 않습니다.

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

## 주요 결정 사항

아키텍처 ADR은 `docs/decisions.md`에 원본으로 누적됩니다. 여기서 요약을 따로 유지하지 않습니다 — 요약은 ADR이 추가될 때마다 갱신을 잊기 쉬워 실제 내용과 어긋나기 쉽습니다.

## 작업 후 의무사항

`AGENTS.md`의 "작업 후 체크리스트"를 따릅니다.
