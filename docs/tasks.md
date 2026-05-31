# TASKS — 백로그

작업 항목은 `T-NNN` 형식의 ID로 관리한다. 새 작업은 "대기"의 우선순위 순서대로 들어가고, 진행 중이 되면 담당자를 표시한다. 완료된 작업은 "완료" 섹션 상단에 누적한다.

## 진행 중

- (없음)

## 대기 (우선순위 순)

- [ ] **T-009** `ApiCatalogEntry`에 중복/대체 경로 메타 추가 — `has_apihub_equivalent: bool` 등 필드로 UI에서 대체 경로 안내.

## 완료

- [x] **T-007** 테스트 갭 보완 — `tests/test_pagination.py` 신설(10개), async generated endpoint 테스트(4개), CLI edge case(6개), timeline edge case(4개) 추가. mock 129 passed. (`_http` retry는 T-006 완료) (2026-05-31)
- [x] **T-006** retry에 jitter 추가 — `_http.py`에 `_backoff_with_jitter()`(equal jitter, `[base/2, base]`) 추가, sync/async retry 양쪽 적용. `tests/test_http.py` 신설(jitter 경계 + retry 단위 테스트 6개). (2026-05-31)
- [x] **T-005** 특보 전용 Pydantic 모델 추가 — `weather_warning_list()`(getWthrWrnList)가 `WeatherWarningItem`를 반환. 라이브 검증으로 WthrWrnInfoService는 구독 확인(6일 조회 제한·NO_DATA 처리 문서화). (2026-05-31)
- [x] **T-004** ASOS 전용 Pydantic 모델 추가 — `asos_daily_weather()`/`asos_hourly_weather()`가 `AsosDailyItem`/`AsosHourlyItem`를 반환. 라이브 검증 시 해당 서비스키가 ASOS 미구독(HTTP 403)이라 skip 처리하고 `docs/live-test-key-issues.md`에 기록. (2026-05-31)
- [x] **T-003** async 패턴 일관화 — `DataGoKrClient.aio()`/`ApiHubClient.aio()`가 전용 async facade(`AsyncDataGoKrClient`/`AsyncApiHubClient`)를 반환. 동기 메서드명과 동일한 코루틴 노출, `async with` 지원, public export 추가. 라이브 facade 테스트 2개 추가. (2026-05-31)
- [x] **T-002** result code 핸들링 통합 — `_raise_for_result_code()`(client)와 `_raise_for_data_gokr_result_code()`(datagokr)의 매핑을 `_http.py`의 `raise_for_kma_result_code()`로 통합. (2026-05-31)
- [x] **T-001** HTTP 에러 핸들링 공통 추출 — 6개 호출부(3 클라이언트 × sync/async)의 HTTP status → 예외 매핑을 `_http.py`의 `raise_for_kma_http_error()` / `raise_for_kma_network_error()`로 통합. 순 98줄 절감, 라이브 테스트 통과. (2026-05-31)
- [x] **T-008** `python-kraddr-base` 의존성 제거 — `LatLon`/`GridPoint`/mapping 기반 위치 입력만 유지하고 외부 DTO 의존을 제거. (2026-05-27)
- [x] `_parsing.py` 공유 파싱 도우미 추출 — ADR-005 (2026-05-23, PR #3)
- [x] 개발 프로세스 문서 도입 — `docs/resume.md`, `docs/journal.md`, `docs/decisions.md`, `docs/tasks.md`, `docs/agent-guide.md` (2026-05-23, PR #3)
