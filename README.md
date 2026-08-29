# python-kma-api

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![GPL-3.0-or-later 라이선스](https://img.shields.io/badge/License-GPL--3.0--or--later-blue.svg)
![Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)

Korea Meteorological Administration(KMA, 기상청) 공공데이터포털과 APIHub를 Python에서 편하게 쓰기 위한 공용 클라이언트 라이브러리입니다.

`python-kma-api`는 `kma`라는 import package를 제공합니다. 특정 앱의 adapter나 DB 스키마를 전제로 하지 않고, `VilageFcstInfoService_2.0`의 초단기실황, 초단기예보, 단기예보 API를 한 인터페이스로 감싸며, 위도/경도와 KMA 격자 좌표 변환, 발표시각 계산, enum 기반 코드 라벨 매핑, provenance metadata, 예외 처리를 함께 제공합니다.

> 이 저장소는 라이브러리 구현과 유지보수를 위한 명세가 함께 들어 있는 초기 패키지입니다. 세부 API 규칙은 [kma-api.md](kma-api.md), 에이전트 구현 규칙은 [SKILL.md](SKILL.md), 작업 운영 규칙은 [AGENTS.md](AGENTS.md)를 참고하세요.

---

## 먼저 읽을 문서

| 필요 정보 | 문서 |
|---|---|
| 빠른 시작, 설치, 사용 예제 | 이 문서(README.md) |
| 단기예보 API 세부 명세와 구현 주의사항 | [kma-api.md](kma-api.md) |
| 구현자/에이전트용 프로젝트 불변조건 | [SKILL.md](SKILL.md) |
| 작업 운영 규칙과 모듈 소유권 | [AGENTS.md](AGENTS.md) |
| 이 라이브러리를 사용하는 외부 소비자 앱을 위한 AI 에이전트 가이드 | [AI_AGENT_GUIDE.md](AI_AGENT_GUIDE.md) |
| 현재 구현 범위와 API 개수 | [docs/api-coverage.md](docs/api-coverage.md) |
| APIHub 470개 함수형 endpoint 목록 | [docs/apihub-endpoints.md](docs/apihub-endpoints.md) |
| APIHub 범용 클라이언트와 탐색 | [docs/apihub.md](docs/apihub.md) |
| data.go.kr 범용 클라이언트 | [docs/datagokr.md](docs/datagokr.md) |
| data.go.kr/APIHub 중복 표 | [docs/datagokr-apihub-overlap.md](docs/datagokr-apihub-overlap.md) |
| 구조적 의사결정 기록(ADR) | [docs/decisions.md](docs/decisions.md) |
| 테스트 작성과 live test 기준 | [docs/testing.md](docs/testing.md) |
| 흔한 오류 증상과 해결책 | [docs/troubleshooting.md](docs/troubleshooting.md) |
| 반복 실수 방지 로그 | [docs/repeated-mistakes.md](docs/repeated-mistakes.md) |
| 에이전트 작업/문서화 표준 | [docs/agent-guide.md](docs/agent-guide.md) |
| 현재 진척도와 다음 작업 | [docs/resume.md](docs/resume.md) |
| 최근 작업 일지 | [docs/journal.md](docs/journal.md) |
| 백로그 | [docs/tasks.md](docs/tasks.md) |
| 라이브 테스트 서비스키 이슈 | [docs/live-test-key-issues.md](docs/live-test-key-issues.md) |
| 로컬 인증키 env 파일 예시 | [.env.example](.env.example) |
| 기여 절차 | [CONTRIBUTING.md](CONTRIBUTING.md) |
| 변경 이력 | [CHANGELOG.md](CHANGELOG.md) |

---

## 핵심 특징

- **공식 단기예보 3종 우선 지원**: `getUltraSrtNcst`, `getUltraSrtFcst`, `getVilageFcst`를 `KmaClient`에서 호출합니다.
- **httpx 기반 sync/async 클라이언트**: 동기 호출은 `KmaClient`, 비동기 호출은 `async with KmaClient.aio(...)` 형태를 사용하며, 예보 API는 `client.forecast.now()`처럼 service facade 아래에 모았습니다.
- **data.go.kr 범용 호출, 기상청 카탈로그, 주요 helper 지원**: `DataGoKrClient`로 `MidFcstInfoService`, `AsosDalyInfoService`, `WthrWrnInfoService` 같은 KMA REST 서비스를 호출하고, 공공데이터포털 `기상청` 검색 전체 페이지의 KMA 항목 86개와 gateway operation 160개를 카탈로그로 조회합니다.
- **APIHub 범용 호출과 함수형 래퍼 지원**: `ApiHubClient`로 임의 path를 호출하고, `ApiHubGeneratedClient`로 공식 목록의 470개 endpoint를 함수 이름으로 호출합니다.
- **API 카탈로그와 디버그 UI 보조**: `api_catalog()`로 데이터셋명, gateway, operation, 인증키 링크가 있는 선택 목록을 얻고 Streamlit 디버그 화면에서 확인할 수 있습니다.
- **표준 위치 타입**: `LatLon`은 WGS84(`EPSG:4326`) 위도/경도, `GridPoint`는 KMA DFS `nx`/`ny`를 표현합니다.
- **좌표 자동 변환**: 사용자는 `location=LatLon(...)`, `location=GridPoint(...)`, mapping, `lat/lon`, `nx/ny` 중 하나를 넘기고, 라이브러리는 KMA LCC DFS 격자로 표준화합니다.
- **명시적 좌표 변환 alias**: 앱 경계에서는 `wgs84_to_kma_grid(latitude, longitude)`, `kma_grid_to_wgs84(nx, ny)`를 사용할 수 있습니다.
- **KST 발표시각 자동 계산**: API별 실제 조회 가능 지연시간을 반영해 `base_date`와 `base_time`을 고릅니다.
- **Pydantic 응답 모델**: 실황, 예보, 중기예보 row, data.go.kr raw row, 해수욕장 날씨 row는 frozen Pydantic 모델로 반환하며 `model_dump()`, `model_dump_json()`, JSON Schema를 사용할 수 있습니다.
- **예보 row 피벗 helper**: category별 row로 흩어진 단기예보를 `ForecastTimepoint` 시간축 객체로 평탄화할 수 있습니다.
- **Provider metadata와 raw 보존**: typed 모델은 원문 `raw`와 sanitized `metadata`를 담을 수 있어 앱이 직접 raw/serving 저장 전략을 선택할 수 있습니다.
- **enum과 코드 라벨 매핑**: `WeatherCategory`, `KmaEndpoint`, `SkyCode`, `ObservedPrecipitationType`, `ForecastPrecipitationType`를 제공하고, 사람이 읽을 수 있는 한국어 라벨도 함께 제공합니다.
- **문자열 범주값 보존**: `PCP`, `SNO`처럼 `"1.0mm 미만"`, `"30.0~50.0mm"` 같은 범주 문자열은 무리하게 숫자로 바꾸지 않습니다.
- **명확한 예외 계층**: 인증, quota/rate limit, 요청, 서버, 파싱 오류를 구분하고 metadata를 제공합니다.
- **Pagination/cache helper**: data.go.kr `pageNo`/`numOfRows`/`totalCount` 기반 helper와 sanitized cache key helper를 제공합니다.
- **네트워크 없는 기본 테스트**: 좌표 변환, 시간 계산, 코드 매핑, 응답 파싱은 mock/fixture 기반으로 검증합니다.

---

## 권장 Public API

여러 프로젝트에서 직접 의존해도 되는 안정 API는 아래 항목입니다. 이 목록은 package-level `kma.__all__`과 맞춰 관리합니다.

| 분류 | 권장 API |
|---|---|
| typed client | `KmaClient`, `AsyncKmaClient`, `DataGoKrClient`, `ApiHubClient` |
| API 카탈로그 | `KMA_DATA_GOKR_DATASETS`, `DataGoKrDatasetSpec`, `ApiCatalogEntry`, `api_catalog` |
| 인증키 로딩 | `api_key_for_gateway`, `env_names_for_gateway`, `load_local_env` |
| 위치 값 객체 | `LatLon`, `GridPoint`, `normalize_location` |
| 좌표 변환 | `to_grid`, `to_latlon`, `wgs84_to_kma_grid`, `kma_grid_to_wgs84` |
| 응답 모델 | `WeatherSnapshot`, `ForecastItem`, `ForecastTimepoint`, `MidForecastItem`, `DataGoKrItem`, `BeachForecastItem`, `BeachWaveHeight`, `BeachWaterTemperature`, `BeachTideItem`, `BeachSunTime`, `ResponseMetadata` |
| timeline/pagination/cache | `pivot_forecast_items`, `has_next_page`, `next_page_no`, `iter_pages`, `make_cache_key`, `base_available_at`, `cache_expire_at`, `latest_mid_fcst_base`, `latest_mid_fcst_time`, `sanitize_request_params` |
| enum/라벨 | `KmaEndpoint`, `WeatherCategory`, `SkyCode`, `ObservedPrecipitationType`, `ForecastPrecipitationType`, `label_for`, `unit_for`, `parse_amount` |
| 예외 | `KmaError`, `KmaAuthError`, `KmaRequestError`, `KmaServerError`, `KmaParseError` |

`ApiHubGeneratedClient`, `APIHUB_ENDPOINTS`, `APIHUB_ATTACHMENTS`도 public API입니다. 다만 공식 APIHub 목록을 생성한 산출물이므로 endpoint 수와 함수 이름은 upstream 목록 갱신에 따라 바뀔 수 있습니다.

위 표에 없는 모듈별 parser/helper는 internal 또는 maintenance API로 보며 하위 호환을 보장하지 않습니다. 모듈 내부의 `_` prefix 함수와 상수, 그리고 `kma.grid`의 LCC DFS 보정 상수(`RE`, `GRID`, `SLAT1`, `SLAT2`, `OLON`, `OLAT`, `XO`, `YO`)는 구현 세부사항입니다. 검증 근거 없이 바꾸지 않지만, 앱 코드는 이 값들에 직접 의존하지 않는 것을 권장합니다.

---

## 시작하기

### 1단계: 인증키 발급

1. [공공데이터포털](https://www.data.go.kr)에 가입하고 로그인합니다.
2. `기상청_단기예보 ((구)_동네예보) 조회서비스` 또는 `VilageFcstInfoService_2.0`을 찾아 활용신청합니다.
3. 마이페이지에서 승인된 인증키를 확인합니다.
4. `kma`는 `httpx`의 `params=` 인코딩을 사용하므로 **Decoding 인증키**를 환경변수에 넣는 것을 권장합니다.

```bash
export DATA_GO_KR_SERVICE_KEY="발급받은_decoding_인증키"
```

Windows PowerShell:

```powershell
$env:DATA_GO_KR_SERVICE_KEY="발급받은_decoding_인증키"
```

로컬 개발에서는 저장소 루트의 `.env` 또는 `.env.local`에 키를 둘 수 있습니다. `KmaClient.from_env()`, `DataGoKrClient.from_env()`, `ApiHubClient.from_env()`는 process env를 먼저 보고, 없으면 로컬 env 파일을 읽습니다. 같은 key가 여러 로컬 파일에 있으면 가까운 디렉터리 값이 우선하고, 같은 디렉터리에서는 `.env.local`이 `.env`보다 우선합니다.

```text
DATA_GO_KR_SERVICE_KEY=<data.go.kr decoded serviceKey>
DATA_GO_KR_SERVICE_KEY=<data.go.kr decoded serviceKey>
KMA_APIHUB_AUTH_KEY=<APIHub authKey>
```

data.go.kr 계열은 `serviceKey`, APIHub 계열은 `authKey`를 사용합니다. 복사/붙여넣기 중 앞뒤 공백이나 줄바꿈이 섞여도 클라이언트 생성 시 제거합니다.

### 2단계: 설치

PyPI 배포 후:

```bash
pip install python-kma-api
```

개발 중인 로컬 저장소에서는:

```bash
pip install -e ".[dev]"
```

### 3단계: 사용

```python
from kma import KmaClient

with KmaClient.from_env() as kma:
    snap = kma.forecast.now(lat=37.5665, lon=126.9780)  # 서울시청
    print(snap.temperature, snap.precipitation_label)

    items = kma.forecast.vilage(lat=37.5665, lon=126.9780)
    for item in items[:5]:
        print(item.forecast_at, item.category, item.value, item.label)
```

비동기 코드는 `python-krheritage-api`와 같은 facade 패턴을 따릅니다.

```python
from kma import KmaClient

async with KmaClient.aio_from_env() as kma:
    snap = await kma.forecast.now(nx=60, ny=127)
    items = await kma.forecast.short(nx=60, ny=127)
```

KMA 예보 응답은 시간대가 아니라 category row 단위로 나뉘어 있으므로, 화면/저장 경계에서는 시간축으로 피벗하면 다루기 쉽습니다.

```python
from kma import WeatherCategory, pivot_forecast_items

timeline = pivot_forecast_items(items)
first = timeline[0]
print(first.forecast_at, first.value(WeatherCategory.TEMPERATURE), first.label("SKY"))
```

격자 좌표를 이미 알고 있다면 `nx`/`ny`를 직접 사용할 수 있습니다.

```python
items = kma.forecast.vilage(nx=60, ny=127)
```

외부 프로그램에서는 위치를 명시적인 값 객체로 넘기는 방식을 권장합니다.

```python
from kma import GridPoint, LatLon

snap = kma.forecast.now(location=LatLon(37.5665, 126.9780))
items = kma.forecast.vilage(location=GridPoint(60, 127))
short = kma.forecast.short(location={"latitude": 37.5665, "longitude": 126.9780})
```

dict 기반 입력도 지원합니다. API 서버나 설정 파일에서 받은 값을 그대로 연결할 때 유용합니다.

```python
kma.forecast.now(location={"latitude": 37.5665, "longitude": 126.9780})
kma.forecast.now(location={"nx": 60, "ny": 127})
```

좌표 변환만 사용할 수도 있습니다. 기존 tuple 기반 API는 하위 호환용으로 유지합니다.

```python
from kma import LatLon, to_grid, to_latlon

nx, ny = to_grid(37.5665, 126.9780)  # (60, 127)
lat, lon = to_latlon(60, 127)

grid = LatLon(37.5665, 126.9780).to_grid()
latlon = grid.to_latlon()
```

앱의 API 저장 경계처럼 필드명이 `latitude`/`longitude`인 곳에서는 의미가 더 분명한 alias를 권장합니다.

```python
from kma import kma_grid_to_wgs84, wgs84_to_kma_grid

grid = wgs84_to_kma_grid(latitude=37.5665, longitude=126.9780)
latlon = kma_grid_to_wgs84(nx=60, ny=127)
```

---

## 제공 API

| 메서드 | KMA endpoint | 반환 | 설명 |
|---|---|---|---|
| `client.forecast.now(...)` | `getUltraSrtNcst` | `WeatherSnapshot` | 초단기실황. 현재 관측값 중심 |
| `client.forecast.short(...)` | `getUltraSrtFcst` | `list[ForecastItem]` | 초단기예보. 대략 향후 6시간 |
| `client.forecast.vilage(...)` | `getVilageFcst` | `list[ForecastItem]` | 단기예보. 대략 향후 3일 |
| `client.forecast.version(ftype, when)` | `getFcstVersion` | `Mapping` | 예보 버전 정보 |

모든 위치 인자는 둘 중 하나만 사용합니다.

- `location=LatLon(...)`: WGS84 위도/경도 값 객체
- `location=GridPoint(...)`: KMA DFS 격자 값 객체
- `location={"lat": ..., "lon": ...}` 또는 `{"latitude": ..., "longitude": ...}`: mapping 기반 WGS84 입력
- `location={"nx": ..., "ny": ...}`: mapping 기반 KMA DFS 입력
- `lat`, `lon`: WGS84 위도/경도
- `nx`, `ny`: KMA 격자 좌표

여러 좌표 형식을 섞으면 `ValueError`를 발생시킵니다.

APIHub 공식 목록 기반 함수형 래퍼는 470개이며, 포맷정보/예제/코드표 첨부 metadata는 77개입니다. 전체 함수명은 [docs/apihub-endpoints.md](docs/apihub-endpoints.md)에 정리되어 있습니다.

### 범용 클라이언트

`data.go.kr`의 다른 KMA 서비스는 `DataGoKrClient`를 사용합니다.

```python
from kma import DataGoKrClient

client = DataGoKrClient.from_env()
items = client.items(
    "MidFcstInfoService",
    "getMidFcst",
    {"stnId": "108", "tmFc": "202605010600"},
)
```

data.go.kr 문서가 인증키 파라미터를 `ServiceKey`로 표기한 서비스는 다음처럼 바꿀 수 있습니다.

```python
client = DataGoKrClient.from_env(service_key_param="ServiceKey")
```

공공데이터포털 `기상청` 오픈 API 검색 전체 페이지에서 확인한 KMA 항목은 카탈로그로 확인할 수 있습니다. 제목이 `기상청`으로 시작하지 않는 검색 결과는 포함하지 않습니다. 카탈로그에는 KMA 항목 86개, 기존 data.go.kr `serviceKey` gateway operation 160개, APIHub LINK 항목 48개가 들어 있습니다.

```python
from kma import KMA_DATA_GOKR_DATASETS, api_catalog

print(len(KMA_DATA_GOKR_DATASETS))  # 86
for entry in api_catalog(gateway="datagokr")[:3]:
    print(entry.dataset_name, entry.operation, entry.service_key_url)

spec = client.dataset("15059093")
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

여러 operation을 가진 dataset은 `operation=`을 명시합니다. APIHub로 연결된 항목은 `gateway="apihub"`로 표시되며 `ApiHubClient` 또는 `ApiHubGeneratedClient`를 사용합니다.

`api_catalog()`는 UI 선택 목록용 `label`, 사람이 읽는 `dataset_name`, 인증 파라미터명(`serviceKey` 또는 `authKey`), 키 발급/확인 링크(`service_key_url`)를 함께 제공합니다.

중기예보는 `DataGoKrClient`의 명시적 helper를 사용할 수 있습니다. `reg_id`는 단기예보의 `nx`/`ny`와 다른 KMA 중기예보 권역 코드이며, `kma`는 임의 매핑을 추측하지 않습니다. `tm_fc`를 생략하면 06:00/18:00 발표와 10분 지연을 반영해 최신 조회 가능 `tmFc`를 고릅니다.

```python
rows = client.mid_land_forecast(reg_id="11B00000", tm_fc="202605010600")
latest_rows = client.mid_land_forecast(reg_id="11B00000")
temps = client.mid_temperature_forecast(reg_id="11B10101", tm_fc="202605010600")
overview = client.mid_forecast(stn_id="108", tm_fc="202605010600")
sea = client.mid_sea_forecast(reg_id="12A20000", tm_fc="202605010600")
asos = client.asos_daily_weather(start_dt="20260501", end_dt="20260502", stn_ids=108)
warnings = client.weather_warning_list(stn_id=108, from_tm_fc="20260501", to_tm_fc="20260502")
situation = client.weather_situation(stn_id=108)
uv = client.uv_index(area_no="1100000000", time="2026050106")
quake = client.earthquake_message_list(from_tm_fc="20260501", to_tm_fc="20260502")
```

해수욕장 날씨 조회서비스(`BeachInfoservice`)는 전용 helper가 있습니다.

```python
beach_forecast = client.beach_forecast(beach_num=1)
ultra = client.beach_ultra_short_forecast(
    beach_num=1,
    base_date="20220622",
    base_time="1230",
)
waves = client.beach_wave_height(beach_num=1, search_time="202205011600")
tides = client.beach_tide_info(beach_num=1, base_date="20220620")
sun = client.beach_sun_info(beach_num=1, base_date="20220501")
water = client.beach_water_temperature(beach_num=1, search_time="202205011600")
```

`beach_forecast()`와 `beach_ultra_short_forecast()`는 `base_date`/`base_time`을 생략하면 KST 기준 최신 발표시각을 자동 선택합니다. `beach_sun_info()`는 공공데이터포털 Swagger의 `Base_date` 파라미터 표기를 그대로 사용합니다.

페이지가 있는 data.go.kr 응답은 helper로 순회할 수 있습니다. `max_pages` 또는 `max_items` guard를 항상 둡니다.

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

APIHub는 별도 인증키(`authKey`)를 사용합니다.

```python
from kma import ApiHubClient, ApiHubGeneratedClient

hub = ApiHubClient.from_env()  # KMA_APIHUB_AUTH_KEY 또는 KMA_APIHUB_KEY
response = hub.request_path(
    "/api/typ01/url/wrn_reg.php",
    {"tmfc": "0"},
)
print(response.text)

generated = ApiHubGeneratedClient.from_env()
asos = generated.kma_sfctm2(tm="202605010900", stn="108", help="1")
rows = asos.text_table().rows
```

자세한 내용은 [docs/datagokr.md](docs/datagokr.md)와 [docs/apihub.md](docs/apihub.md)를 참고하세요.

---

## 응답 모델

사용자에게 반환하는 주요 응답은 Pydantic v2 `BaseModel` 기반의 frozen 모델입니다.

```python
snapshot = kma.now(location=LatLon(37.5665, 126.9780))
payload = snapshot.model_dump(mode="json")
schema = snapshot.model_json_schema()
```

`raw`는 provider 원문 row/payload를 보존하고, `metadata`는 저장/캐시/감사 추적에 필요한 provenance를 담습니다. `serviceKey`, `authKey`, `key` 원문은 `metadata.request_params`, 예외 metadata, repr에 남기지 않습니다.

```python
snapshot = kma.now(nx=60, ny=127)

raw_for_db = snapshot.model_dump(mode="json")
serving_payload = {
    "temperature": raw_for_db["temperature"],
    "observed_at": raw_for_db["observed_at"],
    "source": raw_for_db["metadata"],
}
```

`ResponseMetadata` 주요 필드:

- `provider`: `data.go.kr`, `apihub`
- `service_name`: 예: `VilageFcstInfoService_2.0`, `MidFcstInfoService`
- `endpoint`: 예: `getVilageFcst`, `MidFcstInfoService/getMidLandFcst`
- `request_params`: 인증 파라미터가 제거된 요청 파라미터
- `collected_at`: 응답 수집 시각
- `base_date`, `base_time` 또는 `reference_time`: 조회 기준시각

### `WeatherSnapshot`

```python
from datetime import datetime
from pydantic import BaseModel

class WeatherSnapshot(BaseModel):
    observed_at: datetime
    nx: int
    ny: int
    temperature: float | None
    humidity: int | None
    wind_speed: float | None
    wind_direction: int | None
    precipitation: float | None
    sky_label: str | None
    precipitation_label: str | None
    raw: dict

    @property
    def grid(self) -> GridPoint: ...

    @property
    def latlon(self) -> LatLon: ...
```

### `ForecastItem`

```python
from datetime import datetime
from pydantic import BaseModel

class ForecastItem(BaseModel):
    base_at: datetime
    forecast_at: datetime
    nx: int
    ny: int
    category: WeatherCategory | str
    value: str | float
    label: str | None

    @property
    def category_enum(self) -> WeatherCategory | None: ...

    @property
    def unit(self) -> str | None: ...

    @property
    def grid(self) -> GridPoint: ...

    @property
    def latlon(self) -> LatLon: ...
```

`ForecastItem.category`는 알려진 category일 때 `WeatherCategory` enum으로 들어갑니다. `WeatherCategory`는 `str` 기반 enum이라 `"TMP"` 같은 원문 문자열과 비교할 수 있고 JSON 직렬화도 자연스럽게 동작합니다. 알 수 없는 새 category는 원문 문자열을 보존합니다.

`ForecastItem.value`는 숫자로 안전하게 해석되는 값만 `float`가 됩니다. `PCP`, `SNO` 범주 문자열은 원문을 보존합니다.

### `ForecastTimepoint`

```python
from kma import pivot_forecast_items

points = pivot_forecast_items(kma.forecast(nx=60, ny=127))
print(points[0].forecast_at, points[0].values["TMP"])
```

`ForecastTimepoint`는 같은 `forecast_at`, `nx`, `ny`를 가진 `ForecastItem`을 하나로 묶고 category code를 `values`의 key로 둡니다. `labels`, `units`, `raw_items`, `metadata`도 함께 보존하므로 프론트엔드나 BFF 계층에서 row를 다시 조립하지 않아도 됩니다.

### `MidForecastItem`

```python
from kma import DataGoKrClient

client = DataGoKrClient.from_env()
items = client.mid_land_forecast(reg_id="11B00000", tm_fc="202605010600")
```

`MidForecastItem`은 `MidFcstInfoService` row의 `operation`, `tm_fc`, `reg_id`, `stn_id`, `raw`, `metadata`를 담습니다. 중기예보의 `reg_id`는 단기예보 `nx`/`ny`와 다른 식별자이므로, 라이브러리는 좌표나 권역 매핑을 추측하지 않습니다.

### 위치 타입

```python
from kma import GridPoint, LatLon, normalize_location

seoul = LatLon(37.5665, 126.9780)
grid = seoul.to_grid()          # GridPoint(nx=60, ny=127)
center = grid.to_latlon()       # 격자 중심에 가까운 WGS84 좌표

normalize_location({"lat": 37.5665, "lon": 126.9780})  # GridPoint(60, 127)
normalize_location({"nx": 60, "ny": 127})              # GridPoint(60, 127)
```

- `LatLon.crs`는 `"EPSG:4326"`입니다.
- `GridPoint.grid_system`은 `"KMA_DFS"`입니다.
- `nx`/`ny`는 위도/경도가 아니며, KMA DFS 격자 좌표입니다.
- WGS84 좌표는 항상 `lat/lon` 순서로 다루며, 앱 API나 저장 경계에서는 `latitude/longitude` 이름을 사용해도 같은 의미입니다.

### Public enum

```python
from kma import KmaEndpoint, WeatherCategory, label_for, unit_for

WeatherCategory.TEMPERATURE == "TMP"  # True
unit_for(WeatherCategory.TEMPERATURE)  # "C"

label_for(
    WeatherCategory.PRECIPITATION_TYPE,
    "4",
    endpoint=KmaEndpoint.VILAGE_FCST,
)  # "소나기"
```

---

## Python 타입 정책

KMA API는 대부분의 값을 문자열로 반환합니다. `kma`는 사용자에게 불필요한 캐스팅을 요구하지 않도록 모델 경계에서 변환합니다.

| KMA 원본 | Python 타입 | 예시 |
|---|---|---|
| `baseDate`, `baseTime`, `fcstDate`, `fcstTime` | timezone-aware `datetime` | `20260430` + `1400` -> KST datetime |
| 일반 수치값 | `float` | `"18.4"` -> `18.4` |
| 습도, 풍향 | `int | None` | `"52"` -> `52` |
| `SKY`, `PTY` 코드 | `str` 값 + `label` | `"1"` -> `"맑음"` |
| `PCP`, `SNO` 범주 | `str` | `"1.0mm 미만"` 보존 |
| 빈 값 또는 파싱 불가 값 | `None` 또는 원문 | 모델별로 안전하게 처리 |

강수량/적설량 범주를 대표값으로 바꾸고 싶을 때는 `kma.codes.parse_amount()`를 사용할 수 있습니다.

```python
from kma.codes import parse_amount

parse_amount("1.0mm 미만")   # 0.5
parse_amount("30.0~50.0mm") # 40.0
parse_amount("강수없음")     # 0.0
```

---

## 발표시각 규칙

KMA는 요청한 시각의 데이터를 즉시 제공하지 않습니다. `kma`는 아래 규칙으로 가장 최근의 조회 가능한 발표시각을 자동 선택합니다.

| endpoint | 발표 주기 | 조회 가능 기준 |
|---|---|---|
| `getUltraSrtNcst` | 매시 정각 `HH00` | 발표 후 약 40분 |
| `getUltraSrtFcst` | 매시 30분 `HH30` | 발표 후 약 15분, 즉 대체로 `HH45` 이후 |
| `getVilageFcst` | `0200`, `0500`, `0800`, `1100`, `1400`, `1700`, `2000`, `2300` | 발표 후 약 10분 |

예시:

- KST `14:35`의 초단기실황 최신 기준은 `13:00`
- KST `14:45`의 초단기실황 최신 기준은 `14:00`
- KST `14:44`의 초단기예보 최신 기준은 `13:30`
- KST `14:50`의 초단기예보 최신 기준은 `14:30`
- KST `02:05`의 단기예보 최신 기준은 전날 `23:00`

---

## 주요 코드

### `SKY`

| 코드 | 라벨 |
|---|---|
| `1` | 맑음 |
| `3` | 구름많음 |
| `4` | 흐림 |

### `PTY`

초단기실황(`getUltraSrtNcst`)과 예보(`getUltraSrtFcst`, `getVilageFcst`)의 일부 코드 의미가 다릅니다.

| 코드 | 초단기실황 | 예보 |
|---|---|---|
| `0` | 없음 | 없음 |
| `1` | 비 | 비 |
| `2` | 비/눈 | 비/눈 |
| `3` | 눈 | 눈 |
| `4` | - | 소나기 |
| `5` | 빗방울 | - |
| `6` | 빗방울눈날림 | - |
| `7` | 눈날림 | - |

---

## 좌표계 처리

KMA 단기예보 API의 `nx`, `ny`는 위도/경도가 아니라 LCC DFS 격자 좌표입니다. `kma.grid`는 기상청 공식 변환식을 사용합니다.

검증 기준:

| 위치 | 위도/경도 | 격자 |
|---|---|---|
| 서울시청 | `(37.5665, 126.9780)` | `(60, 127)` |
| 부산시청 | `(35.1796, 129.0756)` | `(98, 76)` |
| 제주시청 | `(33.4996, 126.5312)` | `(53, 38)` |
| 강남역 | `(37.4979, 127.0276)` | `(61, 125)` |

---

## 에러 처리

```text
KmaError
├── KmaAuthError      # 인증키 오류, 승인 안 됨, 만료
├── KmaRequestError   # 잘못된 요청, 4xx, 호출 한도 초과 등
├── KmaServerError    # 5xx, 일시적 API 장애
└── KmaParseError     # 예상과 다른 응답 구조
```

대표 result code 처리:

| 코드 | 의미 | 예외 |
|---|---|---|
| `00` | 정상 | 없음 |
| `03` | 데이터 없음 (NO_DATA) | 없음 — 빈 결과로 정규화 |
| `20` | 서비스 접근 거부 | `KmaAuthError` |
| `22` | 호출 제한 초과 | `KmaRequestError` |
| `30` | 등록되지 않은 서비스키 | `KmaAuthError` |
| `31` | 서비스키 만료 | `KmaAuthError` |
| `99` | 기타 오류 | `KmaServerError` |

모든 `KmaError` 하위 예외는 선택적 metadata 속성을 가질 수 있습니다.

```python
try:
    kma.now(nx=60, ny=127)
except KmaError as exc:
    print(exc.failure_kind, exc.retryable, exc.metadata)
```

`failure_kind`는 `auth`, `quota`, `rate_limit`, `request`, `server`, `parse`, `network` 중 하나로 채워질 수 있습니다. 기존처럼 `except KmaAuthError`, `except KmaRequestError`로 잡는 코드는 그대로 동작합니다.

---

## Pagination과 Cache Key

```python
from kma import cache_expire_at, has_next_page, make_cache_key, next_page_no

body = client.request("MidFcstInfoService", "getMidLandFcst", {...})
if has_next_page(body):
    print(next_page_no(body))

key = make_cache_key(
    "getVilageFcst",
    {"base_date": "20260507", "base_time": "0200", "nx": 60, "ny": 127},
)
expire_at = cache_expire_at("getVilageFcst", "20260507", "0200")
```

`make_cache_key()`는 `serviceKey`, `authKey`, `key`를 제거한 sanitized params를 사용합니다. 같은 endpoint, 같은 기준시각, 같은 `nx`/`ny` 조합이면 인증키가 달라도 같은 cache key가 만들어집니다.

`base_available_at()`은 해당 base가 조회 가능해지는 시각을, `cache_expire_at()`은 다음 발표분이 조회 가능해지는 시각을 KST aware `datetime`으로 반환합니다. 예를 들어 `getVilageFcst`의 `0200` cache는 다음 발표인 `0500`에 10분 지연을 더한 `05:10`에 자연 만료시키면 됩니다.

---

## 명령줄 사용

```bash
kma now --lat 37.5665 --lon 126.9780
kma forecast --lat 37.5665 --lon 126.9780
kma forecast --short --nx 60 --ny 127
```

출력은 기본적으로 JSON입니다.

---

## 개발

```bash
git clone https://github.com/digitie/python-kma-api.git
cd python-kma-api
python -m venv .venv
pip install -e ".[dev]"
python -m pytest
ruff check .
mypy src/kma
```

Streamlit 디버그 화면은 선택 의존성으로 실행합니다.

```bash
pip install -e ".[debug-ui]"
streamlit run tools/debug_streamlit.py
```

Raw Response 탭에는 선택한 API의 필수/선택 파라미터 입력 폼과 인증키를 제외한 request params preview가 표시됩니다. 좌측 메뉴에서는 API 풀네임/설명, 서비스키 링크, 환경변수 키 선택, 요청 timeout, fixture 기본 디렉터리를 조정할 수 있고, 폼에 없는 provider별 파라미터는 `Extra params JSON`으로 추가할 수 있습니다. 실행 후 Pydantic Model 탭에는 row 모델 변환 결과가, Processed Result 탭에는 표 형태 row preview가 표시됩니다. Debug Trace 탭에는 현재 카탈로그 항목, 선택한 데이터셋명, gateway, operation, 인증 파라미터, 키 발급/확인 링크가 표시됩니다.

기본 테스트는 실제 API를 호출하지 않아야 합니다. 실제 KMA 호출 테스트를 추가할 경우 `DATA_GO_KR_SERVICE_KEY`가 있을 때만 실행되도록 별도 marker를 사용하세요.

자세한 테스트 정책은 [docs/testing.md](docs/testing.md), 반복되는 API 함정은 [docs/repeated-mistakes.md](docs/repeated-mistakes.md), 오류별 해결책은 [docs/troubleshooting.md](docs/troubleshooting.md)를 참고하세요.

---

## 프로젝트 파일

이 문서와 프로젝트 문서의 파일 위치는 모두 프로젝트 루트 기준 상대 경로로 적습니다. 예를 들어 `src/kma/client.py`, `docs/testing.md`처럼 쓰고, 작업자 로컬 절대 경로는 문서에 남기지 않습니다. Python docstring과 내부 설명 문구는 한글로 작성하되, 코드 식별자와 API 파라미터 이름은 원문을 유지합니다.

```text
src/kma/
├── __init__.py
├── _credentials.py
├── _http.py
├── apihub.py
├── apihub_endpoints.py
├── catalog.py
├── cli.py
├── client.py
├── codes.py
├── datagokr.py
├── datagokr_catalog.py
├── enums.py
├── exceptions.py
├── grid.py
├── locations.py
├── metadata.py
├── models.py
├── pagination.py
├── py.typed
├── timeline.py
└── time_utils.py
tests/
├── test_apihub.py
├── test_apihub_endpoints.py
├── test_apihub_generator.py
├── test_cli.py
├── test_client.py
├── test_codes.py
├── test_datagokr.py
├── test_enums.py
├── test_grid.py
├── test_live_services.py
├── test_locations.py
├── test_public_api.py
├── test_pydantic_models.py
├── test_time_utils.py
└── test_timeline.py
tools/
└── debug_streamlit.py
```

문서 지도는 상단의 [먼저 읽을 문서](#먼저-읽을-문서) 표를 참고하세요.

---

## 호출 한도와 운영 주의

- 공공데이터포털 활용신청 상태와 일일 호출 한도는 계정/서비스 정책에 따라 달라질 수 있습니다.
- APIHub는 일반회원 기준 일 최대 20,000건/5GB, 기관회원 기준 일 최대 30,000건/50GB로 안내되어 있으며, 시스템 상황에 따라 달라질 수 있습니다.
- 인증키는 2년마다 갱신이 필요할 수 있습니다.
- APIHub 인증키는 가입회원 본인만 사용할 수 있고, `KMA_APIHUB_AUTH_KEY` 또는 `KMA_APIHUB_KEY` 환경변수로 전달합니다.
- 서버가 빈 `items`를 반환하는 경우 대개 `base_time`이 아직 조회 가능하지 않거나 위치/서비스 승인 문제가 원인입니다.
- `serviceKey`가 이미 URL 인코딩된 값인지 Decoding 값인지에 따라 전달 방식이 달라집니다. `params=`에는 Decoding 키를 넣는 것을 권장합니다.
- APIHub 데이터는 공공누리 적용을 받으므로 원천 데이터 이용 조건은 APIHub 안내와 약관을 확인해야 합니다.

---

## 라이선스

GPL-3.0-or-later. 자세한 내용은 [LICENSE](LICENSE)를 참고하세요.

KMA 원천 데이터의 저작권과 이용조건은 기상청 및 공공데이터포털 정책을 따릅니다. `kma`는 데이터를 저장하거나 재배포하지 않고 API 응답을 사용자가 다루기 쉬운 형태로 변환합니다.

---

## 참고 링크

- [공공데이터포털](https://www.data.go.kr)
- [기상청 API허브](https://apihub.kma.go.kr)
- [기상청 API허브 API 소개](https://apihub.kma.go.kr/apiInfo.do)
- `VilageFcstInfoService_2.0` 활용가이드

---

## 변경 이력

- `0.1.0`: 초기 패키지 구조, KMA 단기예보 클라이언트, 좌표 변환, 시간 계산, 문서 보강.
