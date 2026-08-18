# data.go.kr KMA 지원

`kma.KmaClient`는 사용량이 높은 단기예보 서비스를 타입화된 모델로 감싼 클라이언트입니다. `apis.data.go.kr/1360000`의 다른 KMA 공공데이터 서비스는 `DataGoKrClient`로 범용 호출합니다.

공식 확인 출처:

- https://www.data.go.kr/data/15084084/openapi.do
- https://www.data.go.kr/data/15059468/openapi.do
- https://www.data.go.kr/data/15000415/openapi.do
- https://www.data.go.kr/tcs/dss/selectApiDataDetailView.do?publicDataPk=15059093
- https://www.data.go.kr/tcs/dss/selectDataSetList.do?dType=API&keyword=%EA%B8%B0%EC%83%81%EC%B2%AD&sort=reqCo&currentPage=1&perPage=40&pblonsipScopeCode=PBDE07
- 수치모델, 위성, 항공, 특보 등 일부 최신 data.go.kr 항목은 APIHub로 redirect/link됩니다.

## 타입화 클라이언트

```python
from kma import KmaClient

kma = KmaClient.from_env()
kma.now(nx=60, ny=127)
kma.forecast_short(nx=60, ny=127)
kma.forecast(nx=60, ny=127)
```

타입화 클라이언트가 다루는 endpoint:

- `VilageFcstInfoService_2.0/getUltraSrtNcst`
- `VilageFcstInfoService_2.0/getUltraSrtFcst`
- `VilageFcstInfoService_2.0/getVilageFcst`
- `VilageFcstInfoService_2.0/getFcstVersion`

## 범용 클라이언트

```python
from kma import DataGoKrClient

client = DataGoKrClient.from_env()
body = client.request(
    "MidFcstInfoService",
    "getMidFcst",
    {"stnId": "108", "tmFc": "202605010600"},
)
```

표준 `response.body.items.item` 구조를 쓰는 operation은 `items()`를 사용할 수 있습니다.

```python
items = client.items(
    "MidFcstInfoService",
    "getMidFcst",
    {"stnId": "108", "tmFc": "202605010600"},
)
```

metadata가 필요하면 `request_with_metadata()`를 사용합니다. metadata의 `request_params`에는 `serviceKey` 원문이 없습니다.

```python
body, metadata = client.request_with_metadata(
    "MidFcstInfoService",
    "getMidFcst",
    {"stnId": "108", "tmFc": "202605010600"},
)
```

## 기상청 API 카탈로그

2026-05-07 기준 공공데이터포털 `기상청` 오픈 API 검색의 모든 페이지를 확인해, 제목이 `기상청`으로 시작하는 항목만 `KMA_DATA_GOKR_DATASETS`에 담았습니다. 검색어에는 걸리지만 기상청이 아닌 기관의 항목은 제외합니다.

카탈로그 86개 중 기존 data.go.kr `serviceKey` gateway 항목은 38개이며, 포털 상세기능에서 확인한 operation 160개를 함께 보존합니다. APIHub로 연결되는 48개 항목은 `gateway="apihub"`로 구분합니다. APIHub와 정확히 같은 `{service}/{operation}` 조합은 [data.go.kr/APIHub 중복 확인](datagokr-apihub-overlap.md)에 표로 정리했습니다.

```python
from kma import KMA_DATA_GOKR_DATASETS, DataGoKrClient, api_catalog

client = DataGoKrClient.from_env()

print(len(KMA_DATA_GOKR_DATASETS))  # 86
for entry in api_catalog(gateway="datagokr")[:3]:
    print(entry.dataset_name, entry.operation, entry.service_key_url)

asos_spec = client.dataset("15059093")
rows = client.dataset_items(
    "15059093",
    {
        "startDt": "20260501",
        "endDt": "20260502",
        "dataCd": "ASOS",
        "dateCd": "DAY",
    },
)
```

`api_catalog()`는 dataset을 operation 단위 row로 펼쳐 `dataset_name`, `label`, `gateway`, `service`, `operation`, `credential_param`, `service_key_url`을 제공합니다. Streamlit 같은 디버그 UI에서는 `label`을 선택 항목으로 쓰고, 사용자가 선택한 row의 `service_key_url`을 서비스키 발급/확인 링크로 보여주면 됩니다.

`dataset_items()`는 서비스와 operation이 하나로 결정되는 data.go.kr gateway 항목을 바로 호출합니다. 여러 operation을 가진 항목은 `operation=`을 명시합니다.

```python
waves = client.dataset_items(
    "15102239",
    {"beach_num": "1", "searchTime": "202205011600"},
    operation="getWhBuoyBeach",
)
```

카탈로그에는 APIHub로 연결되는 data.go.kr 항목도 `gateway="apihub"`로 남겨 둡니다. 이 항목은 `serviceKey` gateway가 아니므로 `dataset_items()`가 호출하지 않고, `ApiHubClient` 또는 `ApiHubGeneratedClient`를 사용해야 합니다.

기본값:

- `serviceKey=<DATA_GO_KR_SERVICE_KEY>` 또는 `<DATA_GO_KR_SERVICE_KEY>`
- `pageNo=1`
- `numOfRows=10`
- `dataType=JSON`

`from_env()`는 process env를 먼저 보고, 없으면 현재 작업 디렉터리와 부모 디렉터리의 `.env`, `.env.local`을 찾습니다. 같은 key가 여러 로컬 파일에 있으면 가까운 디렉터리 값이 우선하고, 같은 디렉터리에서는 `.env.local`이 `.env`보다 우선합니다. 인증키 값에 복사/붙여넣기 공백이나 줄바꿈이 섞이면 클라이언트 생성 시 제거합니다.

공공데이터포털 문서는 서비스에 따라 인증키 항목을 `serviceKey` 또는 `ServiceKey`로 표기합니다. 기본값은 기존 data.go.kr gateway에서 동작 확인한 `serviceKey`이며, 특정 서비스가 대문자 이름을 요구하면 생성자에서 바꿀 수 있습니다.

```python
client = DataGoKrClient.from_env(service_key_param="ServiceKey")
```

## Pagination helper

data.go.kr 계열 response body가 `pageNo`, `numOfRows`, `totalCount`를 포함하면 다음 helper를 사용할 수 있습니다.

```python
from kma import has_next_page, next_page_no

body = client.request("MidFcstInfoService", "getMidLandFcst", {...})
if has_next_page(body):
    print(next_page_no(body))
```

`DataGoKrClient.iter_pages()`는 `max_pages` 또는 `max_items` guard로 무한 반복을 방지합니다.

```python
for body in client.iter_pages(
    "MidFcstInfoService",
    "getMidLandFcst",
    {"regId": "11B00000", "tmFc": "202605010600"},
    num_of_rows=100,
    max_pages=10,
):
    ...
```

## 중기예보 helper

중기예보는 `MidFcstInfoService` 호출과 row parsing까지만 책임집니다. `reg_id`는 단기예보 `nx`/`ny`와 다른 KMA 중기예보 권역 코드이며, `kma`는 임의 매핑을 추측하지 않습니다. `tm_fc`를 생략하면 06:00/18:00 발표와 10분 조회 지연을 반영한 최신 `tmFc`를 사용합니다.

```python
client.mid_forecast(stn_id="108", tm_fc="202605010600")
client.mid_land_forecast(reg_id="11B00000", tm_fc="202605010600")
client.mid_land_forecast(reg_id="11B00000")  # 최신 조회 가능 tmFc 자동 선택
client.mid_temperature_forecast(reg_id="11B10101", tm_fc="202605010600")
client.mid_sea_forecast(reg_id="12A20000", tm_fc="202605010600")
```

각 row는 `MidForecastItem`이며 `operation`, `tm_fc`, `reg_id`, `stn_id`, `raw`, `metadata`를 제공합니다.

실서버 `MidFcstInfoService` 응답 row는 요청의 `tmFc`를 에코하지 않습니다. `MidForecastItem.tm_fc`는 응답 row에 `tmFc`가 있으면 그 값을 우선하고, 없거나 빈 문자열이면 요청에 실제로 사용한(자동 선택 포함) `tmFc`로 폴백해 항상 발표시각을 식별할 수 있습니다. `raw`에는 폴백 값을 주입하지 않고 응답 원본을 그대로 보존합니다.

## 주요 서비스 helper

2026-05-07에 공공데이터포털 `기상청` 오픈 API 검색에서 확인한 주요 data.go.kr 서비스는 전용 helper를 제공합니다. endpoint별 안정적인 도메인 모델을 확정하기 어려운 서비스는 `DataGoKrItem`으로 감싸며, 각 row의 `raw`와 인증키가 제거된 `metadata`를 보존합니다.

```python
from kma import DataGoKrClient

client = DataGoKrClient.from_env()

daily = client.asos_daily_weather(
    start_dt="20260501",
    end_dt="20260502",
    stn_ids=108,
)
hourly = client.asos_hourly_weather(
    start_dt="20260501",
    start_hh="00",
    end_dt="20260501",
    end_hh="23",
    stn_ids=108,
)
warnings = client.weather_warning_list(
    stn_id=108,
    from_tm_fc="20260501",
    to_tm_fc="20260502",
)
situation = client.weather_situation(stn_id=108)
land = client.land_forecast_message(reg_id="11B10101")
sea = client.sea_forecast_message(reg_id="12A20100")
tour = client.tour_village_forecast(course_id=1, current_date="20260501", hour="09")
climate = client.city_tour_climate_index(city_area_id=1100000000, current_date="20260501", day=3)
uv = client.uv_index(area_no="1100000000", time="2026050106")
air = client.air_diffusion_index(area_no="1100000000", time="2026050106")
sen = client.sensible_temperature_index(
    area_no="1100000000",
    time="2026050106",
    request_code="A41",
)
quake = client.earthquake_message_list(from_tm_fc="20260501", to_tm_fc="20260502")
```

지원 범위:

| service | helper |
|---|---|
| `AsosDalyInfoService/getWthrDataList` | `asos_daily_weather()` |
| `AsosHourlyInfoService/getWthrDataList` | `asos_hourly_weather()` |
| `WthrWrnInfoService/*` | `weather_warning()`, `weather_warning_list()` |
| `VilageFcstMsgService/*` | `forecast_message()`, `weather_situation()`, `land_forecast_message()`, `sea_forecast_message()` |
| `TourStnInfoService1/*` | `tour_village_forecast()`, `city_tour_climate_index()` |
| `LivingWthrIdxServiceV4/*` | `sensible_temperature_index()`, `uv_index()`, `air_diffusion_index()` |
| `EqkInfoService/*` | `earthquake_info()`, `earthquake_message()`, `earthquake_message_list()`, `tsunami_message()`, `tsunami_message_list()` |

`weather_warning()`, `forecast_message()`, `earthquake_info()`는 같은 서비스 안의 다른 operation을 직접 지정할 수 있는 얇은 helper입니다. 표준 `response.body.items.item` 형태를 따르는 경우 raw row wrapper로 반환합니다.

## 해수욕장 날씨 조회 helper

공공데이터포털 `기상청_전국 해수욕장 날씨 조회서비스`
(`BeachInfoservice`)는 `DataGoKrClient`의 전용 helper로 호출할 수 있습니다.

```python
from kma import DataGoKrClient

client = DataGoKrClient.from_env()

ultra = client.beach_ultra_short_forecast(
    beach_num=1,
    base_date="20220622",
    base_time="1230",
)
forecast = client.beach_forecast(beach_num=1)
waves = client.beach_wave_height(beach_num=1, search_time="202205011600")
tides = client.beach_tide_info(beach_num=1, base_date="20220620")
sun = client.beach_sun_info(beach_num=1, base_date="20220501")
water = client.beach_water_temperature(beach_num=1, search_time="202205011600")
```

지원 operation:

| method | service/operation | 반환 모델 |
|---|---|---|
| `beach_ultra_short_forecast()` | `BeachInfoservice/getUltraSrtFcstBeach` | `list[BeachForecastItem]` |
| `beach_forecast()` | `BeachInfoservice/getVilageFcstBeach` | `list[BeachForecastItem]` |
| `beach_wave_height()` | `BeachInfoservice/getWhBuoyBeach` | `list[BeachWaveHeight]` |
| `beach_tide_info()` | `BeachInfoservice/getTideInfoBeach` | `list[BeachTideItem]` |
| `beach_sun_info()` | `BeachInfoservice/getSunInfoBeach` | `list[BeachSunTime]` |
| `beach_water_temperature()` | `BeachInfoservice/getTwBuoyBeach` | `list[BeachWaterTemperature]` |

초단기예보와 단기예보 helper는 `base_date`와 `base_time`을 생략하면 KST 기준 최신 조회 가능 발표시각을 자동 선택합니다. 명시할 때는 두 값을 함께 전달해야 합니다.

주의할 점:

- `beach_num`은 해변코드입니다. 위도/경도나 `nx`/`ny`가 아닙니다.
- 파고와 수온 조회의 `search_time`은 `YYYYMMDDHHMM`입니다.
- 일출일몰 endpoint는 upstream Swagger가 날짜 파라미터를 `Base_date`로 표기하므로 helper가 이 이름을 그대로 사용합니다.
- 모든 모델은 `raw`와 인증키가 제거된 `metadata`를 보존합니다.

실제 서버 테스트에서만 쓰는 인증키는 `.env.local`에 둘 수 있습니다. 이 파일은 `.gitignore`에 포함되어 커밋되지 않습니다.

```text
DATA_GO_KR_SERVICE_KEY=<data.go.kr decoded service key>
DATA_GO_KR_SERVICE_KEY=<data.go.kr decoded service key>
```

## HTTP 200 XML 오류 envelope

`dataType=JSON` 요청이어도 data.go.kr gateway는 quota·인증 오류를 HTTP 200
`OpenAPI_ServiceResponse` XML로 반환할 수 있습니다. `DataGoKrClient`의 동기·비동기
호출은 JSON parse 실패 때 XML의 `returnReasonCode`/`resultCode`를 공통 result-code
정책으로 분류합니다. `03`은 빈 `items`/`totalCount=0`, `22`는
`KmaRequestError(failure_kind="quota", retryable=False)`이며, XML이 아니거나 코드가
없으면 `KmaParseError`입니다.

## data.go.kr 검색에서 확인한 예시

공식 data.go.kr 페이지에서 확인한 KMA REST 서비스 예시는 다음과 같습니다.

| service | operation 예시 | 비고 |
|---|---|---|
| `VilageFcstInfoService_2.0` | `getUltraSrtNcst`, `getVilageFcst` | `KmaClient`가 typed 지원 |
| `MidFcstInfoService` | `getMidFcst`, `getMidTa`, `getMidLandFcst`, `getMidSeaFcst` | generic JSON/XML envelope |
| `WthrWrnInfoService` | `getWthrWrnList` | 기상특보 |
| `AsosDalyInfoService` | `getWthrDataList` | ASOS 일자료 |
| `YdstInfoService` | `getYdstSatlitImg`, `getYdstObs` | 황사정보 |
| `LgtDistrbInfoService` | `getLgtDistrb` | 낙뢰분포도 |
| `CloudSatlitInfoService` | `getGk2acldAll` 등 | 위성자료 경량화 |
| `UppInfoService` | 활용가이드별 operation | 고층기상관측 |

일부 최신 data.go.kr 항목은 기존 `serviceKey` gateway가 아니라 APIHub로 이동하는 LINK 유형입니다. 그런 경우 `ApiHubClient`를 사용합니다.

## 인증키 규칙

`requests params=`로 호출할 때는 Decoding service key를 사용합니다.

```python
DataGoKrClient(service_key="decoded-key")
```

이미 인코딩된 키를 `params=`에 넣으면 다시 인코딩되어 `SERVICE_KEY_IS_NOT_REGISTERED_ERROR`가 발생할 수 있습니다.
