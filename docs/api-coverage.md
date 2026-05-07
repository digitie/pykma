# API 구현 범위

이 문서는 현재 `pykma`가 구현한 API 개수를 명확히 세기 위한 기준입니다.

## 요약

현재 직접 타입화된 모델로 구현한 KMA endpoint는 **4개**이고, data.go.kr `기상청` 검색 전체 페이지에서 확인한 KMA 항목 **86개**를 카탈로그로 제공합니다. 이 중 기존 data.go.kr `serviceKey` gateway 항목은 **38개**, 포털 상세기능에서 확인한 gateway operation은 **160개**, APIHub LINK 항목은 **48개**입니다. 주요 서비스 helper는 **20개 이상**의 operation을 감싸며, 별도로 해수욕장 날씨 조회서비스 helper는 **6개** operation을 감쌉니다. APIHub 공식 목록을 함수형으로 감싼 endpoint는 **470개**입니다. 관련 도로 날씨 API로 한국도로공사 휴게소별 날씨 endpoint **1개**도 타입화했습니다.

| 구분 | 개수 | 설명 |
|---|---:|---|
| 개별 타입화 endpoint | 4개 | `KmaClient`가 Pydantic 모델로 반환하는 단기예보 endpoint |
| data.go.kr 범용 호출 방식 | 1개 계층 | 임의 `{service}/{operation}` 호출 가능 |
| data.go.kr 기상청 카탈로그 | 86개 | 공공데이터포털 `기상청` 검색 전체 페이지에서 제목이 `기상청`으로 시작하는 항목만 포함 |
| data.go.kr serviceKey gateway operation | 160개 | 카탈로그 중 gateway 항목 38개의 포털 상세기능 operation |
| data.go.kr/APIHub 정확 중복 | 109개 | APIHub `/api/typ02/openApi/{service}/{operation}`와 같은 gateway operation |
| data.go.kr 주요 서비스 helper | 20개+ | ASOS, 특보, 통보문, 관광코스, 생활기상지수, 지진정보 등 |
| data.go.kr 해수욕장 날씨 helper | 6개 | `BeachInfoservice` operation을 Pydantic row 모델로 반환 |
| APIHub 범용 호출 방식 | 1개 계층 | 임의 `/api/...` path 호출 가능 |
| APIHub 함수형 래퍼 | 470개 | `apiList.do`와 `generateAPIUrl.do` 기반 함수형 endpoint |
| APIHub 첨부 metadata | 77개 | 포맷정보, 예제, 코드표 등 첨부 링크 |
| APIHub 탐색 기능 | 2개 메서드 | 서비스 목록과 endpoint sample 추출 |
| 위치/코드 타입 계층 | 1개 계층 | `LatLon`, `GridPoint`, `WeatherCategory`, `KmaEndpoint` 등 public helper |
| 한국도로공사 휴게소별 날씨 | 1개 | `ExpresswayRestAreaWeatherClient`가 `RestAreaWeather`로 반환 |

## 타입화 endpoint 4개

`KmaClient`가 직접 편의 메서드와 모델을 제공하는 endpoint입니다.

| 번호 | 메서드 | 서비스 | endpoint | 반환 |
|---:|---|---|---|---|
| 1 | `now()` | `VilageFcstInfoService_2.0` | `getUltraSrtNcst` | `WeatherSnapshot` |
| 2 | `forecast_short()` | `VilageFcstInfoService_2.0` | `getUltraSrtFcst` | `list[ForecastItem]` |
| 3 | `forecast()` | `VilageFcstInfoService_2.0` | `getVilageFcst` | `list[ForecastItem]` |
| 4 | `version()` | `VilageFcstInfoService_2.0` | `getFcstVersion` | raw mapping |

## data.go.kr generic 지원

`DataGoKrClient`는 다음 형태의 KMA gateway endpoint를 호출할 수 있습니다.

```text
http://apis.data.go.kr/1360000/{service}/{operation}
```

예:

```python
client.request("MidFcstInfoService", "getMidFcst", {"stnId": "108", "tmFc": "202605010600"})
```

이 계층은 특정 endpoint를 개별 모델로 구현한 것이 아니라, 표준 data.go.kr envelope를 범용으로 처리합니다. 따라서 “개별 구현 endpoint 개수”에는 넣지 않습니다.

공공데이터포털 문서에는 인증키 파라미터가 `serviceKey` 또는 `ServiceKey`로 섞여 표시됩니다. `DataGoKrClient`는 기본적으로 `serviceKey`를 쓰며, 필요한 경우 `service_key_param="ServiceKey"`로 바꿀 수 있습니다.

## data.go.kr 기상청 카탈로그 86개

2026-05-07 기준 공공데이터포털 `기상청` 오픈 API 검색을 `perPage=40`으로 모든 페이지 확인했고, 제목이 `기상청`으로 시작하는 항목만 `KMA_DATA_GOKR_DATASETS`에 반영했습니다. 기상청이 아닌 기관의 검색 결과는 포함하지 않습니다.

카탈로그 구성은 기존 data.go.kr `serviceKey` gateway 38개, 해당 gateway operation 160개, APIHub LINK 48개입니다. 이 중 APIHub `typ02/openApi`와 정확히 같은 `{service}/{operation}`은 21개 dataset, 109개 operation입니다. 자세한 표는 [data.go.kr/APIHub 중복 확인](datagokr-apihub-overlap.md)에 있습니다.

`DataGoKrClient.dataset(dataset_id)`는 카탈로그 metadata를 반환하고, `dataset_items(dataset_id, ...)`는 기존 `serviceKey` gateway 항목을 `{service}/{operation}` 형태로 호출합니다. APIHub LINK 항목은 `gateway="apihub"`로 표시하며 `ApiHubClient` 또는 `ApiHubGeneratedClient`로 호출해야 합니다.

## data.go.kr 주요 서비스 helper

2026-05-07 기준 공공데이터포털 `기상청` 오픈 API 검색에서 확인한 서비스 중 자주 쓰는 주요 REST 서비스는 `DataGoKrClient` helper로 감쌉니다. 응답 row는 endpoint별 고정 모델 대신 `DataGoKrItem`으로 반환해 `service`, `operation`, `raw`, `metadata`를 제공합니다.

| 서비스 | helper |
|---|---|
| `MidFcstInfoService/getMidSeaFcst` | `mid_sea_forecast()` |
| `AsosDalyInfoService/getWthrDataList` | `asos_daily_weather()` |
| `AsosHourlyInfoService/getWthrDataList` | `asos_hourly_weather()` |
| `WthrWrnInfoService/*` | `weather_warning()`, `weather_warning_list()` |
| `VilageFcstMsgService/*` | `forecast_message()`, `weather_situation()`, `land_forecast_message()`, `sea_forecast_message()` |
| `TourStnInfoService1/*` | `tour_village_forecast()`, `city_tour_climate_index()` |
| `LivingWthrIdxServiceV4/*` | `sensible_temperature_index()`, `uv_index()`, `air_diffusion_index()` |
| `EqkInfoService/*` | `earthquake_info()`, `earthquake_message()`, `earthquake_message_list()`, `tsunami_message()`, `tsunami_message_list()` |

## data.go.kr 해수욕장 날씨 helper 6개

공공데이터포털 `기상청_전국 해수욕장 날씨 조회서비스`는 `BeachInfoservice` 아래 6개 operation을 제공합니다. `DataGoKrClient`는 범용 호출도 가능하지만, 이 서비스는 자주 쓰는 파라미터와 응답 row 모델을 전용 helper로 제공합니다.

| 번호 | 메서드 | endpoint | 반환 |
|---:|---|---|---|
| 1 | `beach_ultra_short_forecast()` | `getUltraSrtFcstBeach` | `list[BeachForecastItem]` |
| 2 | `beach_forecast()` | `getVilageFcstBeach` | `list[BeachForecastItem]` |
| 3 | `beach_wave_height()` | `getWhBuoyBeach` | `list[BeachWaveHeight]` |
| 4 | `beach_tide_info()` | `getTideInfoBeach` | `list[BeachTideItem]` |
| 5 | `beach_sun_info()` | `getSunInfoBeach` | `list[BeachSunTime]` |
| 6 | `beach_water_temperature()` | `getTwBuoyBeach` | `list[BeachWaterTemperature]` |

## APIHub 범용 지원

`ApiHubClient`는 다음 형태의 APIHub path를 호출할 수 있습니다.

```text
https://apihub.kma.go.kr/api/...
```

예:

```python
hub.request_path("/api/typ01/url/wrn_reg.php", {"tmfc": "0"})
```

또한 `typ02/openApi` helper를 제공합니다.

```python
hub.open_api("MidFcstInfoService", "getMidFcst", {"stnId": "108", "tmFc": "202605010600"})
```

APIHub는 텍스트, JSON, XML, 이미지, 바이너리 파일 응답이 섞여 있습니다. `pykma`는 endpoint별 반환 스키마를 모두 Pydantic 모델로 고정하지는 않지만, 공식 목록에서 확인한 endpoint를 `ApiHubGeneratedClient`의 함수형 메서드로 제공합니다.

예:

```python
from pykma import ApiHubGeneratedClient

hub = ApiHubGeneratedClient.from_env()
response = hub.kma_sfctm2(tm="202605010900", stn="108", help="1")
```

전체 목록은 [docs/apihub-endpoints.md](apihub-endpoints.md)에 있습니다.

## APIHub 조사 기준

2026-05-06에 공식 페이지를 다시 확인했습니다.

- `apiInfo.do` 사용자용 제공내역 분류: 13개
- `apiList.do`에서 실제 접근 가능한 wrapper 생성 대상 분류: 13개
- `apiList.do`에서 확인한 서비스: 59개
- 함수형 래퍼 생성 기준: `apiList.do` 본문 예제 URL, `generateAPIUrl.do`의 `urlList`, API URL을 포함한 텍스트 예제 첨부
- 중복 제거한 path/parameter signature: 470개
- 첨부 자료 metadata: 77개

`apiInfo.do`의 제공내역 번호는 사용자 안내용 번호이고, `apiList.do`의 `seqApi`는 포털 내부 라우팅 id입니다. 두 번호 체계가 같다고 가정하지 않습니다.

이 470개는 `ApiHubGeneratedClient`의 함수형 래퍼로 구현되어 있습니다. 다만 응답 row schema를 endpoint별 Pydantic 모델로 모두 고정한 것은 아니며, 응답 종류에 따라 `json()`, `text_table()`, `image()` 등으로 다룹니다.

### 2026-05-06 APIHub 재대조 결과

공식 APIHub를 다시 수집해 로컬 snapshot과 비교했습니다.

| 항목 | 공식 재수집 | 로컬 구현 | 차이 |
|---|---:|---:|---:|
| endpoint signature | 470 | 470 | 0 |
| 함수 이름 | 470 | 470 | 0 |
| 첨부 metadata | 77 | 77 | 0 |

`seqApi` 1~20을 확인했을 때 서비스가 있는 카테고리는 `2~12`, `14`, `15`였고, `13`은 현재 서비스가 없습니다. 따라서 생성 대상 카테고리에서 `13`을 제외한 것은 현재 공식 목록과 일치합니다.

검사 중 `generateAPIUrl.do`가 특정 서비스에서 일시적으로 HTTP 500을 반환하는 경우가 확인되었습니다. `tools/update_apihub_endpoints.py`는 이제 보조 URL 발행 metadata가 실패해도 `apiList.do` 본문과 첨부 예제에서 확인되는 endpoint를 계속 수집합니다. 실제 누락 여부는 최종 signature 비교로 확인합니다.

### data.go.kr 재검토 결과

data.go.kr의 KMA REST API는 `http://apis.data.go.kr/1360000/{service}/{operation}` 형태가 반복됩니다. `DataGoKrClient`는 이 형태를 범용으로 호출하고, 공공데이터포털 `기상청` 검색 전체 페이지에서 확인한 KMA 항목 86개와 gateway operation 160개를 dataset id 카탈로그로 제공합니다. 모든 data.go.kr 서비스를 endpoint별 개별 함수로 생성하지는 않습니다.

현재 보장 범위:

- 표준 `response.header/body` JSON envelope 처리
- 단일 dict/list `items.item` 정규화
- typed result-code exception
- `serviceKey`/`ServiceKey` 인증 파라미터 이름 선택
- 제목이 `기상청`으로 시작하는 data.go.kr 검색 항목 86개와 gateway operation 160개 카탈로그

현재 보장하지 않는 범위:

- data.go.kr의 모든 operation을 endpoint별 Pydantic 모델로 고정 변환
- JSON이 아닌 XML 전용 또는 파일 다운로드 응답의 자동 모델링
- 각 서비스별 필수 파라미터 조합 검증
- APIHub LINK 항목을 `serviceKey` gateway로 자동 변환

## 한국도로공사 휴게소별 날씨

`ExpresswayRestAreaWeatherClient`는 한국도로공사 LINK API인 휴게소별 날씨 정보를 호출합니다.

```text
http://data.ex.co.kr/openapi/restinfo/restWeatherList
```

이 API는 기상청 APIHub나 data.go.kr `1360000` gateway가 아니며, 인증 파라미터는 `key`입니다.

| 메서드 | endpoint | 반환 |
|---|---|---|
| `weather(sdate, std_hour)` | `restWeatherList` | `list[RestAreaWeather]` |
| `latest_weather()` | `restWeatherList` | `list[RestAreaWeather]` |

`latest_weather()`는 최근 시간대가 비어 있을 수 있는 API 특성을 고려해 lookback window 안에서 가장 최근의 비어 있지 않은 응답을 찾는 편의 메서드입니다.

## 답변 기준

“지금 구현해놓은 API가 몇 개냐”는 질문에는 다음처럼 답합니다.

- **직접 타입화 구현 endpoint는 4개입니다.**
- **data.go.kr `기상청` 검색 카탈로그 항목은 86개입니다.**
- **APIHub 함수형 래퍼는 470개입니다.**
- **한국도로공사 휴게소별 날씨 타입화 endpoint는 1개입니다.**
- **범용 클라이언트까지 포함하면 data.go.kr 임의 service/operation과 APIHub `/api/...` path를 호출할 수 있습니다.**
- **APIHub 470개는 endpoint별 함수 이름을 제공하지만, 모든 응답을 endpoint별 Pydantic 모델로 강제 변환하지는 않습니다.**
- **위치/코드 타입 계층은 endpoint 개수를 늘리는 항목은 아니며, 외부 프로그램에서 좌표계와 category 문자열을 안정적으로 다루기 위한 public API입니다.**
