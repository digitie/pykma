# JOURNAL — 작업 일지

새 항목은 항상 파일 맨 위에 추가(역시간순). 기존 항목은 절대 수정하지 않는다 — 잘못된 결정조차 기록으로 남는 것이 가치다.

## 2026-05-27 (codex, python-kraddr-base 의존성 제거)

**작업**: `python-kraddr-base` 런타임 의존성과 외부 장소 DTO 기반 좌표 입력을 제거하고, 자체 `LatLon`/`GridPoint`/mapping 기반 위치 표면으로 정리.

**구현 상세**:
- `pyproject.toml`의 `python-kraddr-base` 의존성을 제거.
- `locations.py`, client/model/timeline 경계에서 외부 DTO와 `.coordinate` 흐름을 제거하고 `latlon`/`grid` helper 중심으로 정리.
- README, `kma-api.md`, 테스트 가이드, resume, tasks, changelog에서 위치 타입 설명을 갱신.
- 관련 테스트를 `LatLon`/`GridPoint`/mapping 입력 기준으로 수정.

**검증**:
- `.venv/bin/python -m pytest -q -s` 통과: 97 passed, 4 skipped.
- `.venv/bin/python -m ruff check .` 통과.
- `.venv/bin/python -m mypy src/kma` 통과.

**다음 작업**: T-001 — HTTP 에러 핸들링 공통 추출.

## 2026-05-23 (claude, 코드 리뷰 + 개발 프로세스 도입)

**작업**: 전체 코드베이스 리뷰 수행 및 python-kraddr-geo 프로젝트의 개발 방향성/방식을 본 프로젝트에 도입.

**구현 상세**:
- `_parsing.py` 공유 모듈 추출: `client.py`와 `datagokr.py`에 중복 정의된 `_float_or_none`, `_int_or_none`, `_str_or_none`을 공통 모듈로 통합.
- 개발 프로세스 문서 도입: `docs/resume.md`(재개 가이드), `docs/journal.md`(작업 일지), `docs/decisions.md`(ADR), `docs/tasks.md`(태스크 백로그), `docs/agent-guide.md`(에이전트 협력 표준) 생성.
- `AGENTS.md` 보강: 작업 후 체크리스트, 작업 시작 전 확인 목록 추가.

**리뷰 주요 발견**:
- HTTP 에러 핸들링 코드가 3개 클라이언트 × 2(sync/async) = 6곳에 ~30% 중복
- result code 핸들링(`_raise_for_result_code` vs `_raise_for_data_gokr_result_code`) 중복
- `DataGoKrClient.aio()`와 `ApiHubClient.aio()`가 별도 async facade 없이 같은 타입 반환
- data.go.kr/APIHub 109개 정확 중복 operation이 잘 문서화되어 있으나 통합 facade나 fallback 없음
- 타입화 모델이 4개 단기예보 endpoint에만 있고, ASOS/특보 등은 `DataGoKrItem(raw=dict)` 범용 wrapper

**다음 작업**: T-001 — HTTP 에러 핸들링 공통 추출.
