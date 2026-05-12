# 한국도로공사 휴게소별 날씨

`kma`는 한국도로공사의 “휴게소별 날씨 정보” LINK API도 호출할 수 있습니다. 이 API는 기상청 APIHub나 data.go.kr `1360000` gateway가 아니라 한국도로공사 `data.ex.co.kr` gateway를 사용합니다.

공식 정보:

- 공공데이터포털 데이터명: `한국도로공사_휴게소별 날씨 정보`
- 기관 URL: `http://data.ex.co.kr/openapi/basicinfo/openApiInfoM?apiId=0508`
- 요청 URL: `http://data.ex.co.kr/openapi/restinfo/restWeatherList`
- 요청 파라미터: `key`, `type`, `sdate`, `stdHour`
- 응답 형식: JSON 또는 XML

## 인증키

로컬에서만 쓰는 인증키는 `.env.local`에 둡니다. 이 파일은 `.gitignore`에 포함되어 커밋되지 않습니다.

```text
EXPRESSWAY_API_KEY=<한국도로공사 API key>
```

코드에서는 다음처럼 읽습니다.

```python
from kma import ExpresswayRestAreaWeatherClient

client = ExpresswayRestAreaWeatherClient.from_env()
```

대체 환경변수 이름으로 `KOREA_EXPRESSWAY_API_KEY`도 지원합니다.

## 사용 예

특정 날짜와 시간대의 휴게소별 날씨를 조회합니다.

```python
from kma import ExpresswayRestAreaWeatherClient

client = ExpresswayRestAreaWeatherClient.from_env()
rows = client.weather(sdate="20210507", std_hour=12)

for row in rows[:3]:
    print(row.unit_name, row.route_name, row.weather, row.temperature)
```

가장 최근의 비어 있지 않은 자료를 찾고 싶으면 `latest_weather()`를 사용합니다.

```python
rows = client.latest_weather(lookback_hours=72)
```

## 반환 모델

`weather()`와 `latest_weather()`는 `RestAreaWeather` 목록을 반환합니다.

주요 필드:

| 필드 | 설명 |
|---|---|
| `observed_at` | KST 기준 관측/제공 시각 |
| `unit_code` | 휴게소 코드 |
| `unit_name` | 휴게소명 |
| `route_no` | 노선번호 |
| `route_name` | 노선명 |
| `direction_code` | 방향 코드 |
| `latitude`, `longitude` | WGS84 좌표 |
| `latlon` | 좌표가 유효할 때 `LatLon` 객체 |
| `coordinate` | 좌표가 유효할 때 `pykrtour.PlaceCoordinate` 객체 |
| `address` | 주소가 유효할 때 `pykrtour.Address` 객체 |
| `measurement_station` | 관측 지점명 |
| `weather` | 날씨 설명 |
| `temperature` | 기온 |
| `humidity` | 습도 |
| `wind_speed` | 풍속 |
| `wind_direction_code` | 풍향 코드 |
| `rainfall` | 강수량 |
| `rainfall_strength` | 강수강도 |
| `new_snow` | 신적설 |
| `snow` | 적설 |
| `cloud` | 운량 |
| `dew_point` | 이슬점 |
| `raw` | 원본 row |
| `metadata` | 인증키가 제거된 provider/request metadata |

한국도로공사 API는 결측값을 `-99`, `-99.0`, `-99.000000` 같은 숫자로 내려보내는 경우가 있습니다. `kma`는 이런 sentinel 값을 모델 필드에서 `None`으로 정규화하고, 원문은 `raw`에 보존합니다.

좌표 원문도 `raw["xValue"]`, `raw["yValue"]`에 그대로 남습니다. 모델의 `coordinate`, `longitude`, `latitude`는 유효한 WGS84 숫자일 때만 채워지고, `-99` 계열 결측값이면 `None`입니다. 장소/POI 저장 경계에서는 `coordinate`의 `pykrtour.PlaceCoordinate`와 `address`의 `pykrtour.Address`를 바로 사용할 수 있습니다.

## 실서버 테스트

실제 서버 테스트는 기본 테스트에서 실행되지 않습니다.

```powershell
$env:KMA_RUN_LIVE="1"
python -m pytest tests/test_live_services.py::test_live_expressway_rest_area_weather_shape
Remove-Item Env:\KMA_RUN_LIVE
```

테스트는 `.env.local`의 `EXPRESSWAY_API_KEY`를 읽고, 최근 72시간 안에서 비어 있지 않은 시간대를 찾아 응답 구조를 검증합니다.
