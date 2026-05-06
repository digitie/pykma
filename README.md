# pykma

Korea Meteorological Administration(KMA, 기상청) 공공데이터포털 단기예보 API를 Python에서 편하게 쓰기 위한 클라이언트 라이브러리입니다.

`pykma`는 `VilageFcstInfoService_2.0`의 초단기실황, 초단기예보, 단기예보 API를 한 인터페이스로 감싸고, 위도/경도와 KMA 격자 좌표 변환, 발표시각 계산, enum 기반 코드 라벨 매핑, 예외 처리를 함께 제공합니다.

> 이 저장소는 라이브러리 구현과 유지보수를 위한 명세가 함께 들어 있는 초기 패키지입니다. 세부 API 규칙은 [kma-api.md](kma-api.md), 에이전트 구현 규칙은 [SKILL.md](SKILL.md), 작업 운영 규칙은 [AGENTS.md](AGENTS.md)를 참고하세요.

---

## 핵심 특징

- **공식 단기예보 3종 우선 지원**: `getUltraSrtNcst`, `getUltraSrtFcst`, `getVilageFcst`를 `KmaClient`에서 호출합니다.
- **data.go.kr 범용 호출 지원**: `DataGoKrClient`로 `MidFcstInfoService`, `WthrWrnInfoService` 같은 다른 KMA REST 서비스를 호출합니다.
- **APIHub 범용 호출과 함수형 래퍼 지원**: `ApiHubClient`로 임의 path를 호출하고, `ApiHubGeneratedClient`로 공식 목록의 470개 endpoint를 함수 이름으로 호출합니다.
- **표준 위치 타입**: `LatLon`은 WGS84(`EPSG:4326`) 위도/경도, `GridPoint`는 KMA DFS `nx`/`ny`를 표현합니다.
- **좌표 자동 변환**: 사용자는 `location=LatLon(...)`, `location=GridPoint(...)`, `lat/lon`, `nx/ny` 중 하나를 넘기고, 라이브러리는 KMA LCC DFS 격자로 표준화합니다.
- **KST 발표시각 자동 계산**: API별 실제 조회 가능 지연시간을 반영해 `base_date`와 `base_time`을 고릅니다.
- **Python 타입과 dataclass 반환**: 현재 실황은 `WeatherSnapshot`, 예보는 `ForecastItem`으로 반환합니다.
- **enum과 코드 라벨 매핑**: `WeatherCategory`, `KmaEndpoint`, `SkyCode`, `ObservedPrecipitationType`, `ForecastPrecipitationType`를 제공하고, 사람이 읽을 수 있는 한국어 라벨도 함께 제공합니다.
- **문자열 범주값 보존**: `PCP`, `SNO`처럼 `"1.0mm 미만"`, `"30.0~50.0mm"` 같은 범주 문자열은 무리하게 숫자로 바꾸지 않습니다.
- **명확한 예외 계층**: 인증, 요청, 서버, 파싱 오류를 구분합니다.
- **네트워크 없는 기본 테스트**: 좌표 변환, 시간 계산, 코드 매핑, 응답 파싱은 mock/fixture 기반으로 검증합니다.

---

## 시작하기

### 1단계: 인증키 발급

1. [공공데이터포털](https://www.data.go.kr)에 가입하고 로그인합니다.
2. `기상청_단기예보 ((구)_동네예보) 조회서비스` 또는 `VilageFcstInfoService_2.0`을 찾아 활용신청합니다.
3. 마이페이지에서 승인된 인증키를 확인합니다.
4. `pykma`는 `requests.get(..., params=...)`를 사용하므로 **Decoding 인증키**를 환경변수에 넣는 것을 권장합니다.

```bash
export KMA_SERVICE_KEY="발급받은_decoding_인증키"
```

Windows PowerShell:

```powershell
$env:KMA_SERVICE_KEY="발급받은_decoding_인증키"
```

### 2단계: 설치

PyPI 배포 후:

```bash
pip install pykma
```

개발 중인 로컬 저장소에서는:

```bash
pip install -e ".[dev]"
```

### 3단계: 사용

```python
from pykma import KmaClient

kma = KmaClient.from_env()

snap = kma.now(lat=37.5665, lon=126.9780)  # 서울시청
print(snap.temperature, snap.precipitation_label)

items = kma.forecast(lat=37.5665, lon=126.9780)
for item in items[:5]:
    print(item.forecast_at, item.category, item.value, item.label)
```

격자 좌표를 이미 알고 있다면 `nx`/`ny`를 직접 사용할 수 있습니다.

```python
items = kma.forecast(nx=60, ny=127)
```

외부 프로그램에서는 위치를 명시적인 값 객체로 넘기는 방식을 권장합니다.

```python
from pykma import GridPoint, LatLon

snap = kma.now(location=LatLon(37.5665, 126.9780))
items = kma.forecast(location=GridPoint(60, 127))
```

dict 기반 입력도 지원합니다. API 서버나 설정 파일에서 받은 값을 그대로 연결할 때 유용합니다.

```python
kma.now(location={"latitude": 37.5665, "longitude": 126.9780})
kma.now(location={"nx": 60, "ny": 127})
```

좌표 변환만 사용할 수도 있습니다.

```python
from pykma import LatLon, to_grid, to_latlon

nx, ny = to_grid(37.5665, 126.9780)  # (60, 127)
lat, lon = to_latlon(60, 127)

grid = LatLon(37.5665, 126.9780).to_grid()
latlon = grid.to_latlon()
```

---

## 제공 API

| 메서드 | KMA endpoint | 반환 | 설명 |
|---|---|---|---|
| `KmaClient.now(...)` | `getUltraSrtNcst` | `WeatherSnapshot` | 초단기실황. 현재 관측값 중심 |
| `KmaClient.forecast_short(...)` | `getUltraSrtFcst` | `list[ForecastItem]` | 초단기예보. 대략 향후 6시간 |
| `KmaClient.forecast(...)` | `getVilageFcst` | `list[ForecastItem]` | 단기예보. 대략 향후 3일 |
| `KmaClient.version(ftype, when)` | `getFcstVersion` | `Mapping` | 예보 버전 정보 |

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
from pykma import DataGoKrClient

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

APIHub는 별도 인증키(`authKey`)를 사용합니다.

```python
from pykma import ApiHubClient, ApiHubGeneratedClient

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

### `WeatherSnapshot`

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class WeatherSnapshot:
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
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class ForecastItem:
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

### 위치 타입

```python
from pykma import GridPoint, LatLon, normalize_location

seoul = LatLon(37.5665, 126.9780)
grid = seoul.to_grid()          # GridPoint(nx=60, ny=127)
center = grid.to_latlon()       # 격자 중심에 가까운 WGS84 좌표

normalize_location({"lat": 37.5665, "lon": 126.9780})  # GridPoint(60, 127)
normalize_location({"nx": 60, "ny": 127})              # GridPoint(60, 127)
```

- `LatLon.crs`는 `"EPSG:4326"`입니다.
- `GridPoint.grid_system`은 `"KMA_DFS"`입니다.
- `nx`/`ny`는 위도/경도가 아니며, KMA DFS 격자 좌표입니다.

### Public enum

```python
from pykma import KmaEndpoint, WeatherCategory, label_for, unit_for

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

KMA API는 대부분의 값을 문자열로 반환합니다. `pykma`는 사용자에게 불필요한 캐스팅을 요구하지 않도록 모델 경계에서 변환합니다.

| KMA 원본 | Python 타입 | 예시 |
|---|---|---|
| `baseDate`, `baseTime`, `fcstDate`, `fcstTime` | timezone-aware `datetime` | `20260430` + `1400` -> KST datetime |
| 일반 수치값 | `float` | `"18.4"` -> `18.4` |
| 습도, 풍향 | `int | None` | `"52"` -> `52` |
| `SKY`, `PTY` 코드 | `str` 값 + `label` | `"1"` -> `"맑음"` |
| `PCP`, `SNO` 범주 | `str` | `"1.0mm 미만"` 보존 |
| 빈 값 또는 파싱 불가 값 | `None` 또는 원문 | 모델별로 안전하게 처리 |

강수량/적설량 범주를 대표값으로 바꾸고 싶을 때는 `pykma.codes.parse_amount()`를 사용할 수 있습니다.

```python
from pykma.codes import parse_amount

parse_amount("1.0mm 미만")   # 0.5
parse_amount("30.0~50.0mm") # 40.0
parse_amount("강수없음")     # 0.0
```

---

## 발표시각 규칙

KMA는 요청한 시각의 데이터를 즉시 제공하지 않습니다. `pykma`는 아래 규칙으로 가장 최근의 조회 가능한 발표시각을 자동 선택합니다.

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

KMA 단기예보 API의 `nx`, `ny`는 위도/경도가 아니라 LCC DFS 격자 좌표입니다. `pykma.grid`는 기상청 공식 변환식을 사용합니다.

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
├── KmaRequestError   # 잘못된 요청, 4xx, NODATA 등
├── KmaServerError    # 5xx, 일시적 API 장애
└── KmaParseError     # 예상과 다른 응답 구조
```

대표 result code 처리:

| 코드 | 의미 | 예외 |
|---|---|---|
| `00` | 정상 | 없음 |
| `03` | 데이터 없음 | `KmaRequestError` |
| `20` | 서비스 접근 거부 | `KmaAuthError` |
| `22` | 호출 제한 초과 | `KmaRequestError` |
| `30` | 등록되지 않은 서비스키 | `KmaAuthError` |
| `31` | 서비스키 만료 | `KmaAuthError` |
| `99` | 기타 오류 | `KmaServerError` |

---

## 명령줄 사용

```bash
pykma now --lat 37.5665 --lon 126.9780
pykma forecast --lat 37.5665 --lon 126.9780
pykma forecast --short --nx 60 --ny 127
```

출력은 기본적으로 JSON입니다.

---

## 개발

```bash
git clone https://github.com/digitie/pykma.git
cd pykma
python -m venv .venv
pip install -e ".[dev]"
python -m pytest
ruff check .
mypy pykma
```

기본 테스트는 실제 API를 호출하지 않아야 합니다. 실제 KMA 호출 테스트를 추가할 경우 `KMA_SERVICE_KEY`가 있을 때만 실행되도록 별도 marker를 사용하세요.

자세한 테스트 정책은 [docs/testing.md](docs/testing.md), 반복되는 API 함정은 [docs/repeated-mistakes.md](docs/repeated-mistakes.md), 오류별 해결책은 [docs/troubleshooting.md](docs/troubleshooting.md)를 참고하세요.

---

## 프로젝트 파일

```text
pykma/
├── __init__.py
├── apihub.py
├── apihub_endpoints.py
├── datagokr.py
├── client.py
├── grid.py
├── time_utils.py
├── codes.py
├── models.py
├── exceptions.py
├── _http.py
└── cli.py
tests/
├── test_client.py
├── test_codes.py
├── test_grid.py
└── test_time_utils.py
```

문서:

- [README.md](README.md): 사용자용 가이드
- [kma-api.md](kma-api.md): API 세부 명세와 구현 주의사항
- [SKILL.md](SKILL.md): 에이전트/구현자용 불변조건
- [AGENTS.md](AGENTS.md): 작업 운영 규칙과 모듈 소유권
- [docs/api-coverage.md](docs/api-coverage.md): 현재 구현 범위와 API 개수
- [docs/apihub-endpoints.md](docs/apihub-endpoints.md): APIHub 470개 함수형 endpoint 목록
- [docs/repeated-mistakes.md](docs/repeated-mistakes.md): 반복 실수 방지 로그
- [docs/apihub.md](docs/apihub.md): APIHub 범용 클라이언트와 탐색
- [docs/datagokr.md](docs/datagokr.md): data.go.kr 범용 클라이언트
- [docs/testing.md](docs/testing.md): 테스트 작성과 live test 기준
- [docs/troubleshooting.md](docs/troubleshooting.md): 흔한 오류 증상과 해결책
- [CONTRIBUTING.md](CONTRIBUTING.md): 기여 절차
- [CHANGELOG.md](CHANGELOG.md): 변경 이력

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

KMA 원천 데이터의 저작권과 이용조건은 기상청 및 공공데이터포털 정책을 따릅니다. `pykma`는 데이터를 저장하거나 재배포하지 않고 API 응답을 사용자가 다루기 쉬운 형태로 변환합니다.

---

## 참고 링크

- [공공데이터포털](https://www.data.go.kr)
- [기상청 API허브](https://apihub.kma.go.kr)
- [기상청 API허브 API 소개](https://apihub.kma.go.kr/apiInfo.do)
- `VilageFcstInfoService_2.0` 활용가이드

---

## 변경 이력

- `0.1.0`: 초기 패키지 구조, KMA 단기예보 클라이언트, 좌표 변환, 시간 계산, 문서 보강.
