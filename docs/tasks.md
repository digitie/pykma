# TASKS — 백로그

작업 항목은 `T-NNN` 형식의 ID로 관리한다. 새 작업은 "대기"의 우선순위 순서대로 들어가고, 진행 중이 되면 담당자를 표시한다. 완료된 작업은 "완료" 섹션 상단에 누적한다.

## 진행 중

- (없음)

## 대기 (우선순위 순)

- [ ] **T-001** HTTP 에러 핸들링 공통 추출 — `client.py`, `datagokr.py`, `apihub.py`의 동일 HTTP status → 예외 매핑 코드를 `_http.py`의 `raise_for_kma_http_error()` 하나로 통합. ~150줄 절감 기대.
- [ ] **T-002** result code 핸들링 통합 — `client.py`의 `_raise_for_result_code()`와 `datagokr.py`의 `_raise_for_data_gokr_result_code()`를 공통 함수로 통합.
- [ ] **T-003** async 패턴 일관화 — `DataGoKrClient.aio()`와 `ApiHubClient.aio()`가 `KmaClient.aio()`처럼 별도 async facade를 반환하도록 변경.
- [ ] **T-004** ASOS 전용 Pydantic 모델 추가 — `asos_daily_weather()`, `asos_hourly_weather()` 반환에 `DataGoKrItem` 대신 전용 타입 모델 적용.
- [ ] **T-005** 특보 전용 Pydantic 모델 추가 — `weather_warning()` 계열 반환에 전용 타입 모델 적용.
- [ ] **T-006** retry에 jitter 추가 — `_http.py`의 exponential backoff에 `random.uniform()` 기반 jitter 적용. thundering herd 방지.
- [ ] **T-007** 테스트 갭 보완 — CLI edge case, `pagination.py` 독립 테스트, `timeline.py` edge case, async generated endpoint 테스트, `_http.py` retry 단위 테스트.
- [ ] **T-009** `ApiCatalogEntry`에 중복/대체 경로 메타 추가 — `has_apihub_equivalent: bool` 등 필드로 UI에서 대체 경로 안내.

## 완료

- [x] **T-008** `python-kraddr-base` 의존성 제거 — `LatLon`/`GridPoint`/mapping 기반 위치 입력만 유지하고 외부 DTO 의존을 제거. (2026-05-27)
- [x] `_parsing.py` 공유 파싱 도우미 추출 — ADR-005 (2026-05-23, PR #3)
- [x] 개발 프로세스 문서 도입 — `docs/resume.md`, `docs/journal.md`, `docs/decisions.md`, `docs/tasks.md`, `docs/agent-guide.md` (2026-05-23, PR #3)
