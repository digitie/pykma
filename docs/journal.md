# JOURNAL — 작업 일지

새 항목은 항상 파일 맨 위에 추가(역시간순). 기존 항목은 절대 수정하지 않는다 — 잘못된 결정조차 기록으로 남는 것이 가치다.

## 2026-05-31 (claude, T-007 테스트 갭 보완)

**작업**: 직접 커버되지 않던 모듈/경로에 단위 테스트 추가.

**구현 상세**:
- `tests/test_pagination.py` 신설(10개): `has_next_page`/`next_page_no` 경계, 문자열 metadata 허용, `iter_pages`의 `max_pages`·`max_items` 안전장치, 인자 검증, `start_page` 반영.
- `tests/test_apihub_endpoints.py`에 async generated 경로 테스트 4개: `acall_endpoint`(authKey 부착, sample params, bare query 순서 보존), `atext_endpoint` 파싱.
- `tests/test_cli.py`에 edge case 6개: 빈 `--param` key 거부, `--param` 값의 `=` 보존, 명시적 `--auth-key`, `now`/`forecast`의 latlon·nx/ny 경로, subcommand 누락.
- `tests/test_timeline.py`에 edge case 4개: 빈 입력, 동일 시간/격자/category 덮어쓰기 + raw 순서 보존, 격자 분리, 미지 category 무단위.

**검증**: mock 129 passed(+24), `ruff`/`mypy` 통과, 라이브 7 passed / 2 skipped 회귀 없음(소스 변경 없음).

**다음 작업**: T-009 — `ApiCatalogEntry` 중복/대체 경로 메타 추가.

## 2026-05-31 (claude, T-006 retry jitter)

**작업**: `_http.py`의 exponential backoff에 jitter를 적용해 thundering herd를 완화.

**구현 상세**:
- `_backoff_with_jitter(backoff_factor, attempt)` 추가. equal jitter로 `[base/2, base]` 구간에서 균등 분포(`base = backoff_factor * 2**attempt`). 기존 고정 backoff 대비 평균 대기는 비슷하게 유지하면서 동시 실패 클라이언트의 lockstep 재시도를 분산.
- sync `get_with_retries`와 async `async_get_with_retries`의 sleep을 헬퍼 호출로 교체.
- mypy `no-any-return` 회피 위해 명시적 `float(...)` 캐스트.

**테스트**:
- `tests/test_http.py` 신설: jitter 경계(`[base/2, base]`) 검증, `random.uniform` monkeypatch 결정성, retry-then-succeed(sync/async), 404 비재시도, 재시도 소진 등 6개.

**검증**:
- mock 105 passed(신규 6), `ruff`/`mypy` 통과.
- 라이브 7 passed / 2 skipped — 회귀 없음.

**다음 작업**: T-007 — 테스트 갭 보완(CLI/pagination/timeline/async generated).

## 2026-05-31 (claude, T-005 특보 전용 Pydantic 모델)

**작업**: `weather_warning_list()`(getWthrWrnList)가 범용 `DataGoKrItem` 대신 전용 타입 모델 `WeatherWarningItem`를 반환하도록 변경.

**구현 상세**:
- `models.py`에 `WeatherWarningItem`(stn_id/tm_fc/seq/title + raw + metadata) 추가. 빈 문자열 `None` 정규화.
- `datagokr.py`에 `_weather_warning_item` 빌더 추가, `weather_warning_list()`가 `_items_with_metadata` + 빌더로 타입 리스트 반환.
- 범용 dispatcher인 `weather_warning(operation, ...)`는 operation별 shape가 제각각이라 `DataGoKrItem` 유지(잘 정의된 list helper에만 타입 모델 적용).
- `__init__.py` export, 기존 mock 테스트를 신규 타입 필드 검증으로 갱신.

**라이브 검증 / 발견**:
- WthrWrnInfoService는 현재 service key로 **구독 확인됨**(ASOS와 달리 403 아님).
- 단, `getWthrWrnList`는 **조회 기간 최대 6일**(초과 시 resultCode 99) 및 활성 특보 없을 때 resultCode 03 `NO_DATA` 반환. 라이브 테스트는 현재 시각 기준 최근 3일로 조회하고 `NO_DATA`를 빈 결과로 정상 처리.
- `docs/live-test-key-issues.md`의 정상 엔드포인트 표에 WthrWrnInfoService와 제약을 기록.

**검증**:
- mock 99 passed, `ruff`/`mypy` 통과.
- 라이브 9개 중 7 passed / 2 skipped(ASOS 미구독).

**다음 작업**: T-006 — retry에 jitter 추가.

## 2026-05-31 (claude, T-004 ASOS 전용 Pydantic 모델 + 라이브 서비스키 이슈 문서화)

**작업**: `asos_daily_weather()`/`asos_hourly_weather()`가 범용 `DataGoKrItem` 대신 전용 타입 모델을 반환하도록 변경하고, 라이브 검증 중 발견한 서비스키 구독 이슈를 문서화.

**구현 상세**:
- `models.py`에 `AsosDailyItem`(stn_id/stn_name/date/avg·min·max_temperature/precipitation/avg_wind_speed/avg_humidity)와 `AsosHourlyItem`(stn_id/stn_name/observed_at/temperature/precipitation/wind_speed/wind_direction/humidity/pressure/sea_level_pressure) 추가. 빈 문자열은 `_float_or_none`/`_str_or_none`으로 `None` 정규화, 원본은 `raw` 보존.
- `datagokr.py`에 `_asos_daily_item`/`_asos_hourly_item` 빌더 추가, 두 helper가 `_items_with_metadata` + 빌더로 타입 리스트 반환.
- `__init__.py` export 및 기존 mock 테스트를 신규 타입 필드 검증으로 갱신.

**라이브 검증 / 서비스키 이슈**:
- 실서버 라이브 테스트 추가(`asos_daily`/`asos_hourly`). 현재 `DATA_GO_KR_SERVICE_KEY`로 호출 시 **HTTP 403 KmaAuthError** — ASOS 일/시간자료 서비스에 활용신청(구독) 미승인.
- 코드 결함이 아니므로 라이브 테스트는 `KmaAuthError`를 잡아 `pytest.skip` 처리(라이브 스위트 green 유지).
- `docs/live-test-key-issues.md` 신설: 게이트웨이별 서비스키 이슈/정상 엔드포인트 표와 갱신 절차 기록.

**결정**: ASOS는 모든 KMA 원본 컬럼을 타입화하지 않고 자주 쓰는 측정값만 노출 + `raw` 보존(MidForecastItem/Beach 모델과 동일 정책). 반환 타입 변경은 공개 API 변경이라 CHANGELOG에 기록.

**검증**:
- mock 99 passed, `ruff`/`mypy` 통과.
- 라이브 8개 중 6 passed / 2 skipped(ASOS 키 미구독).

**다음 작업**: T-005 — 특보 전용 Pydantic 모델 추가.

## 2026-05-31 (claude, T-003 async 패턴 일관화)

**작업**: `DataGoKrClient.aio()`/`ApiHubClient.aio()`가 `KmaClient.aio()`처럼 전용 async facade를 반환하도록 통일.

**구현 상세**:
- `datagokr.py`에 `AsyncDataGoKrClient`, `apihub.py`에 `AsyncApiHubClient` facade 클래스 추가. 동기 클라이언트를 감싸고 동기 메서드와 같은 이름(`request`/`items`/`open_api` 등)의 코루틴을 노출하며 내부적으로 `a`-prefixed 메서드에 위임.
- `aio()`/`aio_from_env()`가 raw 클라이언트 대신 facade를 반환하도록 변경. `__aenter__`/`__aexit__`/`aclose`/`from_env`와 `service_key`/`auth_key`·`config`·`closed` 속성 제공.
- `aiter_pages`는 async generator이므로 facade의 `iter_pages`는 `async def`가 아니라 underlying async generator를 그대로 반환.
- 기존 `a`-prefixed 메서드는 동기 클라이언트에 그대로 유지(직접 호출하는 기존 테스트/사용자 호환).
- `__init__.py`에 두 facade를 export하고 `__all__`에 추가.

**결정**: facade 생성자는 `**kwargs` 위임으로 기본값 drift를 피함. `aio()` 반환 타입 변경은 공개 API 변경이지만 T-003의 명시적 목표이며, datagokr/apihub `aio()`는 테스트/내부에서 사용되지 않아 회귀 위험 없음.

**검증**:
- mock 99 passed(facade 단위 테스트 2개 추가), `ruff`/`mypy` 통과.
- 라이브 테스트 6 passed — `DataGoKrClient.aio().items()`와 `ApiHubClient.aio().open_api()` 실서버 검증 2개 추가.

**다음 작업**: T-004 — ASOS 전용 Pydantic 모델 추가.

## 2026-05-31 (claude, T-002 result code 핸들링 통합)

**작업**: `client.py`의 `_raise_for_result_code()`와 `datagokr.py`의 `_raise_for_data_gokr_result_code()`에 중복돼 있던 result code → 예외 매핑을 `_http.py`의 공통 함수로 통합.

**구현 상세**:
- `_http.py`에 `raise_for_kma_result_code(code, message, *, provider, endpoint, label)` 추가. resultCode 매핑 정책({20,30,31} → auth, {04,99} → server/retryable, 22 → quota/retryable, 그 외 → request)을 단일 함수로 통합.
- `redact_credentials_in_text`를 헬퍼 내부에서 호출하므로 `_http.py`가 `.metadata`를 import (순환 없음 — metadata는 내부 import 없음).
- 두 클라이언트의 기존 private wrapper는 label/provider만 넘기는 얇은 호출로 축소, 호출부 시그니처 보존.
- client.py·datagokr.py의 미사용 예외/`redact_credentials_in_text` import 정리.

**검증**:
- `pytest -m "not integration"` 97 passed, `ruff` / `mypy` 통과.
- 라이브 테스트 4 passed (실서버 회귀 없음).

**다음 작업**: T-003 — async 패턴 일관화.

## 2026-05-31 (claude, T-001 HTTP 에러 핸들링 공통 추출)

**작업**: `client.py`, `datagokr.py`, `apihub.py`의 sync/async 6개 호출부에 중복돼 있던 HTTP status → 예외 매핑 코드를 `_http.py`의 공통 함수로 추출.

**구현 상세**:
- `_http.py`에 `raise_for_kma_http_error(exc, *, provider, endpoint, label, detail="")`와 `raise_for_kma_network_error(*, provider, endpoint, label)` 추가. `NoReturn` 타입으로 선언.
- status 매핑 정책(>=500 → `KmaServerError`/server/retryable, 401·403 → `KmaAuthError`/auth, 429 → `KmaRequestError`/rate_limit/retryable, 그 외 → `KmaRequestError`/request)을 한 곳으로 통합.
- `label`(메시지 prefix: "KMA"/"data.go.kr"/"APIHub")과 `provider`(예외에 저장되는 머신 값)를 분리. APIHub의 본문 에러 메시지는 `detail=` 인자로 suffix 부착.
- `from None`을 헬퍼 내부에서 유지해 기존 예외 chain suppression 동작 보존.
- 6개 호출부를 헬퍼 호출로 교체하고, apihub.py의 미사용 예외 import 정리.

**검증**:
- `pytest -m "not integration"` 97 passed, `ruff check .` / `mypy src/kma` 통과.
- 라이브 테스트 `KMA_RUN_LIVE=1 pytest tests/test_live_services.py` 4 passed (실서버 happy path 회귀 없음).
- `git diff --stat`: 순 98줄 절감 (145 +/243 -).

**다음 작업**: T-002 — result code 핸들링 통합.

## 2026-05-31 (codex, Windows worktree alias 복구 및 CodeGraph ignore 정리)

**작업**: Windows 기준 고정 worktree 경로 alias를 실제 checkout과 다시 맞추고, `.codegraph/`가 Git 상태에 나타나지 않도록 ignore 규칙을 정리.

**구현 상세**:
- Windows에서 기대하는 `F:\dev\kma-codex`, `F:\dev\kma-claude`, `F:\dev\kma-antigravity` 경로가 실제 worktree를 가리키도록 junction을 복구.
- `F:\dev\kma-codex` worktree를 detached HEAD에서 `codex/windows-path-fix` 브랜치로 재연결해 작업 기준 경로를 정상화.
- 루트 `.gitignore`에 `.codegraph/`를 추가해 로컬 CodeGraph 산출물이 `git status`를 오염시키지 않도록 정리.

**검증**:
- `C:\Program Files\Git\cmd\git.exe -C F:/dev/kma-codex status --short --branch` 확인.
- `C:\Program Files\Git\cmd\git.exe -C F:/dev/kma-codex check-ignore -v .codegraph .codegraph/codegraph.db` 확인.

**다음 작업**: T-001 — HTTP 에러 핸들링 공통 추출.

## 2026-05-31 (antigravity, 에이전트 고정 worktree prefix 변경 및 CodeGraph 초기화)

**작업**: 에이전트 고정 worktree의 경로 prefix를 `kma-*`에서 프로젝트 명칭인 `python-kma-api-*`로 전면 개편하고, 로컬 디렉토리에 각 에이전트 전용 worktree 생성 및 `codegraph init -i`를 완료함.

**구현 상세**:
- 실제 Git worktree 생성: detached HEAD 상태로 `python-kma-api-codex`, `python-kma-api-claude`, `python-kma-api-antigravity` 워크트리를 `F:\dev` 아래 구축.
- CodeGraph 초기화: 각 워크트리로 이동하여 `codegraph init -i`로 전체 색인을 수행 (디바이스별 약 1.7초 만에 38개 파일, 1,397개 노드 완벽 색인).
- MCP 및 에이전트 설정 갱신: `.gemini/mcp.json`, `antigravity.json`, `claude.json`, `codex.json`, `.codex/config.toml` 경로를 `F:\dev\python-kma-api-*` 형태로 업데이트.
- 문서 연동: `AGENTS.md` 및 `CLAUDE.md` 내 에이전트 worktree 설명 수정.
- 형상 관리: `feat/python-kma-api-worktrees` 브랜치를 생성하여 PR #7 발급, `main` 브랜치에 로컬 머지 후 push 및 임시 브랜치 완벽 정리.

**검증**:
- `git worktree list`를 통해 3개 워크트리 실제 등록 확인.
- 각 워크트리 내부 `.codegraph/` 색인 데이터 존재 확인.
- 품질 게이트 (`pytest -q`, `ruff check`, `mypy`) 무사 통과.

**다음 작업**: T-001 — HTTP 에러 핸들링 공통 추출.

## 2026-05-31 (antigravity, maplibre-vworld-js 스타일 및 MCP 설정 도입)

**작업**: `maplibre-vworld-js` 프로젝트의 에이전트 개발 스타일, 고정 worktree 정책, AI용 가이드 문서, 그리고 MCP 설정을 가져와서 본 프로젝트에 적합하게 적용 및 PR 머지 완료.

**구현 상세**:
- MCP 서버 설정 도입: `.gemini/mcp.json`, `antigravity.json`, `claude.json`, `codex.json`, `.codex/config.toml` 신설 (각각 kma-antigravity, kma-claude, kma-codex worktree 및 codegraph CWD 연동).
- 에이전트 실행 권한 확장: `.claude/settings.local.json`을 수정하여 git, ruff, mypy, pytest 등의 실행 권한 추가.
- 에이전트 개발 가이드 및 스타일 문서 도입:
  - `AGENTS.md` 업데이트 (에이전트 고정 worktree 규칙, 개발 환경 정책, DO NOT 목록 보강).
  - `CLAUDE.md` 신설 (프로젝트 빠른 컨텍스트, 에이전트 고정 worktree 및 품질 검증 명령어 명시).
  - `AI_AGENT_GUIDE.md` 신설 (소비자 앱 AI 어시스턴트 컨텍스트 가이드).
- 품질 검증: `pytest`, `ruff check`, `mypy src/kma` 로컬품질 통과 확인.
- 형상 관리: `feat/style-and-mcp-settings` 브랜치를 생성하여 푸시 후 `gh pr create`로 PR #6 생성, `main` 브랜치에 로컬 머지(FF) 후 push 및 브랜치 정리 완수.

**검증**:
- `.venv/bin/python -m pytest -q` 통과: 97 passed, 4 skipped.
- `ruff check .` 통과.
- `mypy src/kma` 통과.

**다음 작업**: T-001 — HTTP 에러 핸들링 공통 추출.

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
