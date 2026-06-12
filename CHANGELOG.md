# 변경 이력

`python-kma-api`의 주요 변경 사항을 기록합니다.

## 0.1.0 - 미배포

### 수정

- 중기예보 `MidForecastItem.tm_fc`가 live에서 항상 `None`이 되던 결함 수정 (#20). 실서버 `MidFcstInfoService` 응답 row는 요청의 `tmFc`를 에코하지 않으므로, 응답 row에 `tmFc`가 없거나 빈 문자열이면 요청에 실제로 사용한 해석된 `tmFc`(자동 선택 포함)로 폴백한다. 응답 row에 `tmFc`가 있으면 그 값을 우선하고, `raw`에는 폴백 값을 주입하지 않는다. `_mid_items`를 타는 `getMidFcst`/`getMidLandFcst`/`getMidTa`/`getMidSeaFcst` 전부에 적용.
- data.go.kr result code `03`(NODATA_ERROR)을 `KmaRequestError` 대신 **정상적인 빈 결과**로 정규화 (#18). `DataGoKrClient`(특보 `weather_warning_list`, 중기예보 등)와 `KmaClient`(단기예보) 공통 unwrap 단계에서 `body.items.item = []`, `totalCount = 0`으로 반환하므로 특보 없는 평시 구간 rolling-window 조회가 빈 list로 떨어진다. 인증(`20`/`30`/`31`)·서버(`04`/`99`)·기타 오류 코드 정책은 기존과 동일.

### 변경

- Windows 기준 고정 worktree 경로 운용에서 `.codegraph/` 로컬 산출물이 Git 상태에 나타나지 않도록 루트 `.gitignore`를 정리.
- `DataGoKrClient.aio()`/`aio_from_env()`와 `ApiHubClient.aio()`/`aio_from_env()`가 `KmaClient.aio()`처럼 전용 async facade(`AsyncDataGoKrClient`, `AsyncApiHubClient`)를 반환하도록 변경. facade는 동기 메서드와 같은 이름의 코루틴을 노출하며 `async with`를 지원. (기존 `a`-prefixed 메서드는 동기 클라이언트에 그대로 유지)
- `DataGoKrClient.asos_daily_weather()`/`asos_hourly_weather()`가 범용 `DataGoKrItem` 대신 전용 타입 모델 `AsosDailyItem`/`AsosHourlyItem` 리스트를 반환하도록 변경. 자주 쓰는 측정값을 타입화하고 빈 문자열은 `None`으로 정규화하며 원본은 `raw`에 보존.
- `DataGoKrClient.weather_warning_list()`가 범용 `DataGoKrItem` 대신 전용 타입 모델 `WeatherWarningItem` 리스트를 반환하도록 변경.
- 재시도 backoff에 equal jitter를 적용해 동시 실패한 클라이언트들이 같은 시점에 몰려 재시도하는 thundering herd를 완화 (sleep 구간 `[base/2, base]`).

### 추가

- `ApiCatalogEntry`에 `has_apihub_equivalent: bool`과 `apihub_equivalent_path: str | None` 필드를 추가해, data.go.kr operation이 APIHub `typ02/openApi`에도 같은 경로로 존재하는지 UI에서 안내 가능. `asdict()`에도 반영.
- 전용 async facade 클래스 `AsyncDataGoKrClient`, `AsyncApiHubClient`를 public export에 추가.
- ASOS 일/시간 자료 전용 Pydantic 모델 `AsosDailyItem`, `AsosHourlyItem`를 public export에 추가.
- 기상특보 목록 전용 Pydantic 모델 `WeatherWarningItem`를 public export에 추가.

- `getUltraSrtNcst`, `getUltraSrtFcst`, `getVilageFcst`, `getFcstVersion`을 다루는 초기 `KmaClient`.
- KMA LCC DFS 격자 변환 함수 `to_grid()`, `to_latlon()`.
- 초단기실황, 초단기예보, 단기예보 발표시각을 KST 기준으로 계산하는 helper.
- endpoint별 `SKY`, `PTY` 라벨 매핑.
- `PCP`, `SNO`의 한국어 범주 문자열을 보존하는 안전한 값 처리.
- 인증, 요청, 서버, 파싱 오류를 구분하는 예외 계층.
- JSON 출력 CLI.
- `apis.data.go.kr/1360000`의 다른 KMA 서비스 호출을 위한 `DataGoKrClient`.
- APIHub `authKey` 호출, `typ02/openApi` helper, 포털 탐색 parser를 제공하는 `ApiHubClient`.
- APIHub 공식 목록 기반 470개 함수형 endpoint 래퍼를 제공하는 `ApiHubGeneratedClient`.
- APIHub TXT 응답을 row 구조로 바꾸는 `text_table()`과 이미지 bytes에서 포맷/크기를 읽는 `image()` helper.
- APIHub path를 호출하는 CLI 명령.
- APIHub endpoint 래퍼를 재생성하는 `tools/update_apihub_endpoints.py`와 전체 함수 목록 문서.
- 클라이언트 파싱, 시간 규칙, 좌표 변환, 코드 매핑, APIHub 래퍼, CLI 동작을 검증하는 오프라인 단위 테스트.
- `.env.local`과 `KMA_RUN_LIVE=1`로만 실행되는 APIHub/data.go.kr 실서버 integration 테스트.
- APIHub 401/403을 `KmaAuthError`로 변환하고 응답 URL/예외에서 인증키를 가리는 보호 로직.
- 외부 프로그램에서 좌표계를 명확히 다룰 수 있는 `LatLon`, `GridPoint`, `normalize_location()` public API.
- KMA endpoint/category/code 문자열 오타를 줄이는 `KmaEndpoint`, `WeatherCategory`, `SkyCode`, `ObservedPrecipitationType`, `ForecastPrecipitationType` enum.
- `ForecastItem`과 `WeatherSnapshot`의 `grid`, `latlon`, `category_enum`, `unit` helper 속성.
- data.go.kr 문서의 `serviceKey`/`ServiceKey` 표기 차이를 처리할 수 있는 `service_key_param` 설정.
- public 응답 모델을 frozen Pydantic v2 모델로 전환하고 `model_dump()`, `model_dump_json()`, JSON Schema를 지원.
- 권장 public API 목록과 `__all__` 정렬.
- 명시적 좌표 변환 alias `wgs84_to_kma_grid()`, `kma_grid_to_wgs84()`.
- provider provenance를 담는 `ResponseMetadata`와 인증 파라미터를 제거하는 `sanitize_request_params()`.
- sanitized params 기반 `make_cache_key()`와 data.go.kr pagination helper.
- `ForecastItem` row를 시간대별 `ForecastTimepoint`로 묶는 `pivot_forecast_items()` helper.
- 발표주기 기반 `base_available_at()`, `cache_expire_at()`, 중기예보 `latest_mid_fcst_base()`/`latest_mid_fcst_time()` helper.
- 중기예보 row를 보존하는 `MidForecastItem` 및 `DataGoKrClient.mid_*` helper.
- 공공데이터포털 `기상청` 오픈 API 검색에서 확인한 주요 미구현 서비스(ASOS, 특보, 통보문, 관광코스, 생활기상지수, 지진정보)를 감싸는 `DataGoKrClient` helper와 `DataGoKrItem` 모델.
- 공공데이터포털 `기상청` 오픈 API 검색 전체 페이지에서 제목이 `기상청`으로 시작하는 86개 항목만 담은 `KMA_DATA_GOKR_DATASETS` 카탈로그와, 기존 `serviceKey` gateway 38개/operation 160개를 dataset id로 호출하는 helper.
- 공공데이터포털 `BeachInfoservice` 6개 operation을 감싸는 `DataGoKrClient.beach_*` helper와 해수욕장 row 모델.
- `KmaError` 계층의 `failure_kind`, `retryable`, provider/endpoint/status/result metadata.
- 복사/붙여넣기 공백을 제거하는 인증키 정규화와 `.env`/`.env.local` 로컬 키 로딩.
- 데이터셋명, gateway, operation, 인증키 링크를 제공하는 `api_catalog()`와 선택 실행용 Streamlit 디버그 화면.
- README, API 레퍼런스, 에이전트 가이드, 트러블슈팅, 테스트 가이드, 반복 실수 방지 문서.

### 제거

- `python-kraddr-base` 런타임 의존성과 외부 장소 DTO 기반 위치 입력 지원을 제거. 좌표 입력은 `LatLon`, `GridPoint`, mapping, `lat/lon`, `nx`/`ny`로 제공.
- 비기상청 도로 날씨 클라이언트와 관련 테스트/문서를 제거. 해당 기능은 `python-krex-api`에서 관리.
