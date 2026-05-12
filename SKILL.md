---
name: kma-api-python-builder
description: 기상청 공공 날씨 API와 관련 도로 날씨 API용 Python 클라이언트를 구현, 확장, 디버그, 테스트할 때 사용한다. KMA, 기상청, 단기예보, 초단기실황, 초단기예보, 동네예보, VilageFcstInfoService_2.0, APIHub, data.go.kr, 한국도로공사, 휴게소별 날씨, nx/ny 격자 변환, base_time 계산, serviceKey/authKey/key 인코딩, SKY/PTY 코드, apis.data.go.kr/1360000, apihub.kma.go.kr, data.ex.co.kr 관련 작업에 적용한다.
---

# KMA Python 라이브러리 빌더

`python-kma-api`는 기상청 공공 날씨 API와 관련 도로 날씨 API를 위한 Python 클라이언트이며 import package 이름은 `kma`입니다. public 동작을 바꾸기 전 `README.md`, `kma-api.md`, `docs/api-coverage.md`, `docs/apihub.md`, `docs/apihub-endpoints.md`, `docs/datagokr.md`, `docs/expressway.md`, `AGENTS.md`를 확인합니다.

## 프로젝트 불변조건

1. 타입화된 클라이언트의 1차 대상은 `VilageFcstInfoService_2.0`입니다.
2. data.go.kr 기본 URL은 `http://apis.data.go.kr/1360000`입니다.
3. data.go.kr 인증 파라미터는 `serviceKey`입니다.
4. data.go.kr에서 `requests params=`를 쓸 때는 Decoding 키를 권장합니다.
5. data.go.kr user-facing 메서드는 기본적으로 `dataType=JSON`을 요청합니다.
6. APIHub 기본 URL은 `https://apihub.kma.go.kr`입니다.
7. APIHub 인증 파라미터는 `authKey`입니다.
8. 한국도로공사 휴게소 날씨 기본 URL은 `http://data.ex.co.kr/openapi/restinfo/restWeatherList`입니다.
9. 한국도로공사 휴게소 날씨 인증 파라미터는 `key`입니다.
10. KMA 예보 시간과 도로 날씨 조회 시각은 KST(UTC+9)입니다. naive `datetime`은 KST로 해석합니다.
11. public API는 `location=LatLon(...)`, `location=GridPoint(...)`, WGS84 `lat`/`lon`, KMA 격자 `nx`/`ny` 중 하나를 받습니다. `nx`/`ny`를 위도/경도로 취급하지 않습니다.
12. KMA `resultCode != "00"`은 typed exception으로 surface합니다.
13. 기본 테스트는 실제 KMA/APIHub/도로공사 API를 호출하지 않습니다.
14. APIHub 응답은 JSON, XML, 텍스트, 이미지, 바이너리가 섞여 있으므로 하나의 모델로 강제하지 않습니다.
15. APIHub legacy 그래픽 URL의 이름 없는 query string은 순서가 의미이므로 `arg1`, `arg2` 순서를 보존합니다.
16. 문서의 파일 위치 정보는 프로젝트 루트 기준 상대 경로로 작성하고, 로컬 절대 경로는 남기지 않습니다.
17. Python docstring과 내부 설명 문구는 한글로 작성하되, 코드 식별자와 API 파라미터 이름은 원문을 유지합니다.
18. `rg`가 실행 권한 문제로 실패하면 검색 결과가 없다고 판단하지 말고 PowerShell `Get-ChildItem`/`Select-String`으로 우회합니다.
19. PowerShell에서 한글 Markdown을 확인할 때는 UTF-8 출력을 명시하고 `Get-Content -Encoding UTF8`을 사용합니다.
20. 편의용 wrapper를 불필요하게 늘리지 않습니다. 단순 전달 계층은 기존 범용 클라이언트를 쓰고, 안정적인 public surface와 테스트 가능한 동작이 있을 때만 wrapper를 추가합니다.
21. 다른 라이브러리에 검증된 구현이 있으면 라이선스와 출처를 확인한 뒤 adapter/wrapper로 감싸기보다 프로젝트 코드에 직접 반영합니다. 이 변경이 최소수정 원칙보다 커져도 동작 일치, 테스트 가능성, 장기 유지보수성을 우선합니다.

## 현재 구현 범위

정확한 구현 개수는 `docs/api-coverage.md`를 기준으로 합니다.

- 개별 타입화 KMA endpoint: 4개
- data.go.kr 범용 호출 계층: 임의 `{service}/{operation}` 호출 가능
- APIHub 범용 호출 계층: 임의 `/api/...` path 호출 가능
- APIHub 함수형 래퍼: 공식 목록 기반 470개 endpoint
- APIHub 탐색 기능: 공식 페이지에서 서비스 목록과 sample endpoint signature 추출 가능
- 한국도로공사 휴게소별 날씨: 1개 endpoint typed 모델 지원

## 지원 endpoint

타입화된 클라이언트가 직접 모델링한 endpoint:

| public method | endpoint | 목적 |
|---|---|---|
| `KmaClient.now()` | `getUltraSrtNcst` | 초단기실황 |
| `KmaClient.forecast_short()` | `getUltraSrtFcst` | 초단기예보 |
| `KmaClient.forecast()` | `getVilageFcst` | 단기예보 |
| `KmaClient.version()` | `getFcstVersion` | 예보버전 |
| `ExpresswayRestAreaWeatherClient.weather()` | `restWeatherList` | 휴게소별 날씨 |

그 외 KMA 서비스는 우선 범용 클라이언트로 호출합니다. 안정적인 응답 schema와 사용례가 쌓이고 public API 가치가 분명할 때만 타입화된 wrapper를 추가합니다. 단순히 다른 호출을 감싸는 wrapper는 만들지 않으며, 다른 라이브러리의 검증된 구현을 가져와야 할 때는 라이선스와 출처를 확인한 뒤 프로젝트 내부 구현으로 직접 흡수합니다.

## 처음부터 구현할 때 필요한 산출물

```text
src/kma/
├── __init__.py          # public client, model, exception, 좌표 helper export
├── client.py            # KmaClient 타입화 단기예보 client
├── datagokr.py          # DataGoKrClient data.go.kr 범용 client
├── datagokr_catalog.py  # 공공데이터포털 기상청 OpenAPI dataset catalog
├── apihub.py            # ApiHubClient APIHub 범용 client, 탐색, TXT/이미지 helper
├── apihub_endpoints.py  # 생성된 APIHub 함수형 endpoint 래퍼
├── expressway.py        # 한국도로공사 휴게소별 날씨 client
├── enums.py             # KmaEndpoint, WeatherCategory, SKY/PTY enum
├── locations.py         # LatLon, GridPoint, normalize_location
├── grid.py              # KMA LCC DFS 변환
├── time_utils.py        # KST 기준 base time helper
├── codes.py             # SKY/PTY map, category unit, parse_amount
├── models.py            # frozen Pydantic response models
├── exceptions.py        # KmaError 계층
├── _http.py             # requests session과 retry 설정
└── cli.py               # console entrypoint
tests/
├── test_client.py
├── test_datagokr.py
├── test_apihub.py
├── test_apihub_endpoints.py
├── test_expressway.py
├── test_codes.py
├── test_enums.py
├── test_grid.py
├── test_locations.py
├── test_time_utils.py
└── test_cli.py
```

## Public API 규칙

### `KmaClient`

```python
KmaClient(service_key, *, timeout=10, retries=3, base_url=None, session=None)
KmaClient.from_env(name="KMA_SERVICE_KEY")
```

위치 인자는 다음 형식 중 하나만 받습니다.

```python
kma.now(location=LatLon(37.5665, 126.9780))
kma.now(location=GridPoint(60, 127))
kma.now(location={"latitude": 37.5665, "longitude": 126.9780})
kma.now(location={"nx": 60, "ny": 127})
kma.now(lat=37.5665, lon=126.9780)
kma.now(nx=60, ny=127)
```

거부해야 하는 입력:

- `lat`만 있고 `lon` 없음
- `nx`만 있고 `ny` 없음
- `lat/lon`과 `nx/ny`를 동시에 전달
- `location`과 `lat/lon` 또는 `nx/ny`를 동시에 전달

### 위치와 enum

- `LatLon`은 WGS84 좌표이며 `crs == "EPSG:4326"`입니다.
- `GridPoint`는 KMA DFS 좌표이며 `grid_system == "KMA_DFS"`입니다.
- `normalize_location()`은 외부 dict/object 입력을 `GridPoint`로 표준화하는 경계 함수입니다.
- `WeatherCategory`, `KmaEndpoint`, `SkyCode`, `ObservedPrecipitationType`, `ForecastPrecipitationType`는 KMA wire value와 같은 `str` enum입니다.
- 알려진 `ForecastItem.category`는 `WeatherCategory`로 반환하고, 알 수 없는 새 category는 문자열 원문을 보존합니다.
- enum 값은 JSON 직렬화와 문자열 비교가 자연스럽게 동작해야 합니다.

### `DataGoKrClient`

```python
DataGoKrClient(service_key)
client.request("MidFcstInfoService", "getMidFcst", {"stnId": "108", "tmFc": "202605010600"})
client.items("MidFcstInfoService", "getMidFcst", {...})
```

규칙:

- `serviceKey`를 자동으로 보냅니다.
- 문서가 `ServiceKey`를 요구하는 경우 `service_key_param="ServiceKey"`를 사용할 수 있어야 합니다.
- 기본값은 `pageNo=1`, `numOfRows=10`, `dataType=JSON`입니다.
- `items()`는 단일 dict를 list로 감쌉니다.

### `ApiHubClient`

```python
ApiHubClient(auth_key)
hub.request_path("/api/typ01/url/wrn_reg.php", {"tmfc": "0"})
hub.open_api("MidFcstInfoService", "getMidFcst", {"stnId": "108", "tmFc": "202605010600"})
```

규칙:

- `/api/`로 시작하는 path만 허용합니다.
- `authKey`를 자동으로 보냅니다.
- JSON으로 확정된 endpoint가 아니면 `response.text` 또는 `response.content`를 사용합니다.
- TXT 응답은 `response.text_table()`로 Python row 구조를 만들 수 있습니다.
- 이미지 응답은 `response.image()`로 bytes, format, width, height를 얻을 수 있습니다.

### `ApiHubGeneratedClient`

```python
from kma import ApiHubGeneratedClient

hub = ApiHubGeneratedClient.from_env()
hub.kma_sfctm2(tm="202605010900", stn="108", help="1")
hub.aws3_nph_awsm_tms_h06(use_sample=True)
```

규칙:

- 함수형 wrapper 목록은 `tools/update_apihub_endpoints.py`로 생성합니다.
- 생성 결과는 `src/kma/apihub_endpoints.py`와 `docs/apihub-endpoints.md`가 함께 바뀌어야 합니다.
- 포맷정보/예제/코드표 첨부 링크는 `APIHUB_ATTACHMENTS`에 metadata로 남깁니다.
- 예제 URL의 `authKey`는 버리고 사용자의 `authKey`만 붙입니다.
- 이름 없는 query string은 `request_query_parts()`를 통해 순서를 보존합니다.

### `ExpresswayRestAreaWeatherClient`

```python
ExpresswayRestAreaWeatherClient(api_key)
ExpresswayRestAreaWeatherClient.from_env(name="EXPRESSWAY_API_KEY")
client.weather(sdate="20210507", std_hour=12)
client.latest_weather(lookback_hours=72)
```

규칙:

- `key`, `type=json`, `sdate`, `stdHour`를 요청 파라미터로 보냅니다.
- `sdate`는 `YYYYMMDD`, `stdHour`는 `00`~`23`으로 표준화합니다.
- 응답의 `code`가 `SUCCESS`가 아니면 typed exception입니다.
- 메시지에 인증키 문제가 있으면 `KmaAuthError`입니다.
- `-99`, `-99.0`, `-99.000000` 계열 결측값은 `RestAreaWeather` 필드에서 `None`으로 정규화합니다.
- 원본 row는 `RestAreaWeather.raw`에 보존합니다.

## 타입 변환 정책

KMA 응답은 문자열 중심입니다. 모델 경계에서 변환하되 의미 있는 라벨은 보존합니다.

| 원본 필드/값 | Python 표면 | 규칙 |
|---|---|---|
| `baseDate` + `baseTime` | aware `datetime` | KST timezone |
| `fcstDate` + `fcstTime` | aware `datetime` | KST timezone |
| 일반 수치 category | `float` | 안전할 때 `float()` |
| snapshot의 습도/풍향 | `int | None` | float 파싱 후 int |
| `SKY` | raw 값과 label | `1`, `3`, `4` |
| `PTY` | endpoint-aware label | 실황과 예보 map이 다름 |
| `PCP`, `SNO` | `str` | 범주 라벨 보존 |
| 실황 `RN1` | `float | None` | `parse_amount()` 사용 |
| 잘못된 수치 | field별 raw string 또는 `None` | optional 파싱에서 crash하지 않음 |

## `PCP`, `SNO`를 무조건 float로 바꾸지 말 것

예시:

- `강수없음`
- `적설없음`
- `1.0mm 미만`
- `30.0~50.0mm`
- `50.0mm 이상`

`ForecastItem.value`에서는 문자열을 보존합니다. 대표값이 필요할 때만 `parse_amount()`를 제공합니다.

## 발표시각 규칙

### `getUltraSrtNcst`

- 매시 `HH00` 발표.
- 보통 발표 후 40분부터 조회 가능.
- KST `14:35`에는 `13:00` 사용.
- KST `14:45`에는 `14:00` 사용.

### `getUltraSrtFcst`

- 매시 `HH30` 발표.
- 보통 발표 후 15분, 즉 `HH45`부터 조회 가능.
- KST `14:44`에는 `13:30` 사용.
- KST `14:50`에는 `14:30` 사용.

### `getVilageFcst`

- `0200`, `0500`, `0800`, `1100`, `1400`, `1700`, `2000`, `2300` 발표.
- 보통 발표 후 10분부터 조회 가능.
- `02:10` 이전에는 전날 `2300` 사용.

## 격자 변환 규칙

KMA는 Lambert Conformal Conic DFS 격자를 사용합니다.

상수:

```python
RE = 6371.00877
GRID = 5.0
SLAT1 = 30.0
SLAT2 = 60.0
OLON = 126.0
OLAT = 38.0
XO = 43
YO = 136
```

검증점:

| 위치 | WGS84 | KMA 격자 |
|---|---|---|
| 서울시청 | `(37.5665, 126.9780)` | `(60, 127)` |
| 부산시청 | `(35.1796, 129.0756)` | `(98, 76)` |
| 제주시청 | `(33.4996, 126.5312)` | `(53, 38)` |
| 강남역 | `(37.4979, 127.0276)` | `(61, 125)` |

근거 없이 상수를 바꾸지 않습니다.

## 코드 매핑 규칙

### `SKY`

```python
{"1": "맑음", "3": "구름많음", "4": "흐림"}
```

`2`를 임의로 만들지 않습니다.

### `PTY`

초단기실황(`getUltraSrtNcst`):

```python
{
    "0": "없음",
    "1": "비",
    "2": "비/눈",
    "3": "눈",
    "5": "빗방울",
    "6": "빗방울눈날림",
    "7": "눈날림",
}
```

예보(`getUltraSrtFcst`, `getVilageFcst`):

```python
{
    "0": "없음",
    "1": "비",
    "2": "비/눈",
    "3": "눈",
    "4": "소나기",
}
```

반드시 endpoint-aware로 매핑합니다.

## 예외 계층

```text
KmaError
├── KmaAuthError
├── KmaRequestError
├── KmaServerError
└── KmaParseError
```

대표 result code 처리:

| 코드 | 처리 |
|---|---|
| `00` | 성공 |
| `03` | `KmaRequestError` |
| `04` | `KmaServerError` |
| `12` | `KmaRequestError` |
| `20` | `KmaAuthError` |
| `22` | `KmaRequestError` |
| `30` | `KmaAuthError` |
| `31` | `KmaAuthError` |
| `99` | `KmaServerError` |

잘못된 JSON이나 예상과 다른 응답 구조는 `KmaParseError`입니다.

## HTTP 계층 규칙

- session/retry 설정은 `src/kma/_http.py` 한 곳에서 관리합니다.
- transient GET 실패(`429`, `500`, `502`, `503`, `504`)만 retry합니다.
- 인증 실패를 retry하지 않습니다.
- 인증키를 로그로 남기지 않습니다.
- 테스트를 위해 `session=` 주입을 허용합니다.

## 테스트 규칙

필수 오프라인 테스트:

- 격자 변환 검증점
- 격자 역변환 허용 오차
- base time helper와 자정 경계
- `SKY`/`PTY` endpoint-aware 라벨
- `PCP`/`SNO` 보존
- `parse_amount()` 범위 문자열
- fake session 기반 요청 파라미터
- result code 예외 매핑
- data.go.kr 범용 envelope 처리
- APIHub sample URL parser와 탐색 parser
- APIHub 생성 래퍼 개수, 함수 호출, 이름 없는 query string 보존
- TXT table parser와 이미지 header parser

실제 API 테스트:

- `integration` marker 사용
- `KMA_SERVICE_KEY` 또는 `KMA_APIHUB_AUTH_KEY`가 없으면 skip
- 정확한 날씨값이 아니라 응답 구조와 타입만 검증

## 흔한 함정

1. Encoding service key를 `params=`에 넣으면 이중 인코딩될 수 있습니다.
2. 현재 시각을 그대로 `base_time`으로 쓰면 빈 데이터가 자주 나옵니다.
3. `nx`/`ny`를 WGS84 좌표로 취급하면 안 됩니다.
4. `PCP`/`SNO`에 `float()`를 직접 적용하면 한국어 범주 라벨에서 실패합니다.
5. `PTY=4`의 의미는 endpoint마다 다릅니다.
6. raw API dict를 그대로 반환하면 KMA 응답 구조가 사용자 코드로 새어 나갑니다.
7. PowerShell mojibake만 보고 UTF-8 파일이 깨졌다고 판단하면 불필요한 변경이 생깁니다.
8. APIHub와 data.go.kr의 인증 파라미터를 섞으면 인증 실패가 납니다.
9. APIHub endpoint가 항상 JSON이라고 가정하면 텍스트/이미지/파일 endpoint에서 실패합니다.
10. APIHub의 이름 없는 query string을 `params=` mapping으로 바꾸면 그래픽 endpoint URL이 달라집니다.
11. `apiList.do` 본문만 긁으면 `generateAPIUrl.do`나 텍스트 예제 첨부에만 있는 endpoint를 놓칠 수 있습니다.
12. `rg` 실행 권한 오류를 빈 검색 결과로 착각하면 필요한 파일을 놓칠 수 있습니다.

함정을 수정하면 `docs/repeated-mistakes.md`에 증상, 규칙, 방지 테스트를 기록합니다.

## 문서 갱신 규칙

- 사용자-facing API가 바뀌면 `README.md`를 갱신합니다.
- 파일 위치 정보는 `src/kma/client.py`, `docs/testing.md`처럼 프로젝트 루트 기준 상대 경로로 작성합니다.
- Python 내부 문서와 docstring은 한글로 작성합니다.
- endpoint 세부 사항이나 KMA 동작이 바뀌면 `kma-api.md`를 갱신합니다.
- APIHub 분류, 탐색 기능, 응답 형식 규칙이 바뀌면 `docs/apihub.md`를 갱신합니다.
- APIHub 함수형 endpoint 목록이 바뀌면 `tools/update_apihub_endpoints.py`를 실행하고 `docs/apihub-endpoints.md`를 함께 갱신합니다.
- data.go.kr 범용 처리 방식이 바뀌면 `docs/datagokr.md`를 갱신합니다.
- 구현 범위나 API 개수가 바뀌면 `docs/api-coverage.md`를 갱신합니다.
- 테스트 전략, marker, fixture 정책이 바뀌면 `docs/testing.md`를 갱신합니다.
- 사용자에게 보이는 오류 해결책이 생기면 `docs/troubleshooting.md`를 갱신합니다.
- 반복 실수가 발견되거나 예방되면 `docs/repeated-mistakes.md`를 갱신합니다.
- 릴리스 관점의 추가/수정/호환성 변경은 `CHANGELOG.md`에 기록합니다.
