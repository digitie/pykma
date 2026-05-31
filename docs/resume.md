# RESUME — 작업 재개 가이드

새 에이전트 세션이 시작될 때 "지금 어디까지 했고, 다음은 뭐 하면 되나"를 한 화면에서 답한다.

## 현재 진척도 (2026-05-27 갱신)

- ✅ Windows 기준 고정 worktree alias 복구 및 `.codegraph/` Git 상태 노이즈 제거
- ✅ `KmaClient` 타입화 단기예보 4개 endpoint (`getUltraSrtNcst`, `getUltraSrtFcst`, `getVilageFcst`, `getFcstVersion`)
- ✅ `DataGoKrClient` data.go.kr 범용 `{service}/{operation}` 호출 + 86개 dataset 카탈로그
- ✅ `DataGoKrClient` 주요 서비스 helper 20개+ (중기예보, ASOS, 특보, 통보문, 관광, 생활기상지수, 지진/쓰나미)
- ✅ `DataGoKrClient` 해수욕장 날씨 helper 6개 (전용 Pydantic 모델)
- ✅ `ApiHubClient` 범용 path 호출 + 탐색 기능 (서비스 목록, endpoint sample 추출)
- ✅ `ApiHubGeneratedClient` 470개 함수형 endpoint wrapper
- ✅ data.go.kr/APIHub 중복 109개 operation 문서화 (`docs/datagokr-apihub-overlap.md`)
- ✅ 좌표 변환 (WGS84 ↔ KMA LCC DFS 격자), `LatLon`/`GridPoint`
- ✅ 외부 장소 DTO 의존성 제거, `LatLon`/`GridPoint`/mapping 기반 위치 입력으로 정리
- ✅ `ForecastTimepoint` 피벗 + `pivot_forecast_items()` 시계열 helper
- ✅ 예외 계층 (`KmaError` → `Auth`/`Request`/`Server`/`Parse`)
- ✅ 인증값 보안 (redaction, sanitize, `.env` 로딩)
- ✅ 142개 테스트 (130 mock + 12 live, 라이브는 키 구독에 따라 일부 skip), ruff/mypy 통과
- ✅ httpx async facade (`build_session`, `build_async_client`, sync/async retry)
- ✅ `_parsing.py` 공유 파싱 도우미 추출 (PR #3)
- ✅ `maplibre-vworld-js` 에이전트 스타일, 고정 worktree 규칙, AI용 가이드 문서, MCP 설정 도입 및 PR 머지 완료
- ✅ 에이전트 고정 워크트리(`python-kma-api-*`) 실제 생성 및 CodeGraph 색인(`codegraph init -i`) 완료
- ✅ HTTP 에러 핸들링 공통 추출 — `raise_for_kma_http_error()` / `raise_for_kma_network_error()` (T-001, 6곳 통합)
- ✅ result code 핸들링 통합 — `raise_for_kma_result_code()` (T-002)
- ✅ async 패턴 일관화 — `AsyncDataGoKrClient`/`AsyncApiHubClient` facade, `aio()` 반환 변경 (T-003)
- ✅ ASOS helper 전용 Pydantic 모델 — `AsosDailyItem`/`AsosHourlyItem` (T-004)
- ✅ 특보 전용 Pydantic 모델 — `WeatherWarningItem`, `weather_warning_list()` 적용 (T-005)
- ✅ retry에 jitter 추가 — `_backoff_with_jitter()` equal jitter (T-006)
- ✅ 테스트 갭 보완 — pagination/async generated/CLI/timeline edge case (T-007, `_http` retry는 T-006)
- ✅ `ApiCatalogEntry` 대체 경로 메타 — `has_apihub_equivalent`/`apihub_equivalent_path` (T-009)
- ✅ 라이브 테스트 확대(중기예보/통보문/단기예보) + 서비스키 구독 상태 실측 문서화 (`docs/live-test-key-issues.md`)

## 다음 한 작업 (1시간 이내 분량)

`docs/tasks.md`의 백로그가 모두 비었다(T-001~T-009 완료). 다음 후보:
- ASOS·통보문(VilageFcstMsgService) 서비스키 활용신청 후 `docs/live-test-key-issues.md`의 skip 테스트 재검증.
- 라이브 커버리지 추가 확대(지진/태풍/생활기상지수 등) 및 서비스키 이슈 지속 기록.
- HTTP 에러/parse 핸들링의 추가 통합 여지 검토.

## 작업 시작 전 확인할 것

- [ ] `AGENTS.md`의 "반드시 지킬 것"과 "모듈 지도" 다시 읽기
- [ ] `SKILL.md` "프로젝트 불변조건" 다시 읽기
- [ ] `docs/api-coverage.md`의 현재 구현 범위 확인
- [ ] 마지막 `docs/journal.md` 엔트리 읽기
- [ ] 관련 `docs/decisions.md` ADR 확인

## 알려진 함정

- **좌표 입력 범위**: 외부 장소 DTO를 직접 받지 않습니다. 앱 경계에서는 `LatLon`, `GridPoint`, 또는 `{"latitude": ..., "longitude": ...}` mapping으로 변환한 뒤 넘깁니다.
- **data.go.kr 인증키 인코딩**: `params=`로 보낼 때는 Decoding 키를 써야 이중 인코딩 방지. Encoding 키를 쓰면 `SERVICE_KEY_IS_NOT_REGISTERED_ERROR`.
- **KMA 시간 경계**: 자정 직후 `getVilageFcst`는 전날 2300 base를 사용해야 함. `latest_vilage_base()`가 처리.
- **`PTY` 코드 차이**: 실황(`getUltraSrtNcst`)과 예보(`getVilageFcst`)에서 코드 의미가 다름.
- **APIHub 텍스트 응답**: APIHub endpoint는 JSON을 반환한다고 가정하면 안 됨. `response_kind`로 확인.
- **data.go.kr/APIHub 인증 분리**: 같은 operation이라도 `serviceKey` vs `authKey`가 다름. 두 gateway를 섞지 않는다.

## 작업 후 의무사항

1. `docs/journal.md`에 항목 추가 (날짜·요약·관련 파일·결정·다음 작업)
2. 본 `docs/resume.md`의 진척도 토글 갱신
3. 변경된 결정이 있다면 `docs/decisions.md`에 ADR 추가
4. 사용자 가시 변경이면 `CHANGELOG.md` 갱신
5. `pytest` / `ruff check .` / `mypy src/kma` 통과 확인
