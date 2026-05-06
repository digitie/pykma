# 변경 이력

`pykma`의 주요 변경 사항을 기록합니다.

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
- `.env.local`과 `PYKMA_RUN_LIVE=1`로만 실행되는 APIHub/data.go.kr 실서버 integration 테스트.
- APIHub 401/403을 `KmaAuthError`로 변환하고 응답 URL/예외에서 인증키를 가리는 보호 로직.
- 외부 프로그램에서 좌표계를 명확히 다룰 수 있는 `LatLon`, `GridPoint`, `normalize_location()` public API.
- KMA endpoint/category/code 문자열 오타를 줄이는 `KmaEndpoint`, `WeatherCategory`, `SkyCode`, `ObservedPrecipitationType`, `ForecastPrecipitationType` enum.
- `ForecastItem`과 `WeatherSnapshot`의 `grid`, `latlon`, `category_enum`, `unit` helper 속성.
- data.go.kr 문서의 `serviceKey`/`ServiceKey` 표기 차이를 처리할 수 있는 `service_key_param` 설정.
- README, API 레퍼런스, 에이전트 가이드, 트러블슈팅, 테스트 가이드, 반복 실수 방지 문서.
