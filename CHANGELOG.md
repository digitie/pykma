# 변경 이력

`python-kma-api`의 주요 변경 사항을 기록합니다.

## 0.1.0 - 미배포

### 추가

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

- 비기상청 도로 날씨 클라이언트와 관련 테스트/문서를 제거. 해당 기능은 `python-krex-api`에서 관리.
