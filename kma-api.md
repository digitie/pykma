# KMA 단기예보 API 명세

> 이 문서는 `kma` 구현자를 위한 API 레퍼런스입니다. 사용자용 빠른 설명은 `README.md`, 에이전트 구현 규칙은 `SKILL.md`를 보세요.

APIHub 전체 범위와 generic 호출 방식은 [docs/apihub.md](docs/apihub.md), APIHub 함수형 endpoint 목록은 [docs/apihub-endpoints.md](docs/apihub-endpoints.md), data.go.kr generic 호출 방식은 [docs/datagokr.md](docs/datagokr.md)를 함께 보세요.

## 1. 개요

| 항목 | 값 |
|---|---|
| 서비스 | 기상청 단기예보 조회서비스 |
| 공공데이터포털 서비스명 | `VilageFcstInfoService_2.0` |
| Base URL | `http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0` |
| 인증 파라미터 | `serviceKey` |
| 출력 형식 | `dataType=JSON` |
| 기본 페이지 | `pageNo=1` |
| 권장 row 수 | `numOfRows=1000` |
| 시간대 | KST(UTC+9) |
| 좌표계 | KMA LCC DFS 격자 `nx`, `ny` |

## 2. 인증키 처리

공공데이터포털은 Encoding 키와 Decoding 키를 함께 보여줍니다.

`kma`의 기본 HTTP 호출은 다음 형태입니다.

```python
requests.get(url, params={"serviceKey": service_key, ...})
```

따라서 `service_key`에는 **Decoding 키**를 넣는 것을 권장합니다. 이미 URL 인코딩된 Encoding 키를 `params=`에 넣으면 다시 인코딩되어 `SERVICE_KEY_IS_NOT_REGISTERED_ERROR`가 발생할 수 있습니다.

URL 문자열에 직접 붙여야 하는 디버깅 상황에서는 Encoding 키를 사용할 수 있지만, 라이브러리의 일반 경로에서는 Decoding 키를 기준으로 합니다.

## 3. 공통 요청 파라미터

초단기실황, 초단기예보, 단기예보의 공통 파라미터:

| 파라미터 | 필수 | 설명 |
|---|---|---|
| `serviceKey` | 예 | 공공데이터포털 인증키 |
| `pageNo` | 예 | 보통 `1` |
| `numOfRows` | 예 | `getVilageFcst`는 항목이 많으므로 `1000` 권장 |
| `dataType` | 예 | `JSON` |
| `base_date` | 예 | 발표일, `YYYYMMDD` |
| `base_time` | 예 | 발표시각, `HHMM` |
| `nx` | 예 | KMA 격자 X |
| `ny` | 예 | KMA 격자 Y |

## 4. Endpoint 목록

### 4.1 `getUltraSrtNcst`

초단기실황입니다. 격자 기준 현재 관측값을 반환합니다.

| 항목 | 값 |
|---|---|
| public method | `KmaClient.now()` |
| 발표시각 | 매시 정각 `HH00` |
| 조회 가능 | 발표 후 약 40분 |
| 시간 필드 | `baseDate`, `baseTime` |
| 값 필드 | `obsrValue` |
| 반환 모델 | `WeatherSnapshot` |

대표 category:

| 코드 | 의미 | 단위 |
|---|---|---|
| `T1H` | 기온 | C |
| `RN1` | 1시간 강수량 | mm 또는 범주 |
| `UUU` | 동서바람성분 | m/s |
| `VVV` | 남북바람성분 | m/s |
| `REH` | 습도 | % |
| `PTY` | 강수형태 | code |
| `VEC` | 풍향 | deg |
| `WSD` | 풍속 | m/s |

### 4.2 `getUltraSrtFcst`

초단기예보입니다. 대략 향후 6시간의 시간별 예보를 반환합니다.

| 항목 | 값 |
|---|---|
| public method | `KmaClient.forecast_short()` |
| 발표시각 | 매시 30분 `HH30` |
| 조회 가능 | 발표 후 약 15분, 보통 `HH45` 이후 |
| 시간 필드 | `baseDate`, `baseTime`, `fcstDate`, `fcstTime` |
| 값 필드 | `fcstValue` |
| 반환 모델 | `list[ForecastItem]` |

대표 category:

| 코드 | 의미 | 단위 |
|---|---|---|
| `T1H` | 기온 | C |
| `RN1` | 1시간 강수량 | mm 또는 범주 |
| `SKY` | 하늘상태 | code |
| `UUU` | 동서바람성분 | m/s |
| `VVV` | 남북바람성분 | m/s |
| `REH` | 습도 | % |
| `PTY` | 강수형태 | code |
| `LGT` | 낙뢰 | code |
| `VEC` | 풍향 | deg |
| `WSD` | 풍속 | m/s |

### 4.3 `getVilageFcst`

단기예보입니다. 대략 3일 범위의 예보 항목을 반환합니다.

| 항목 | 값 |
|---|---|
| public method | `KmaClient.forecast()` |
| 발표시각 | `0200`, `0500`, `0800`, `1100`, `1400`, `1700`, `2000`, `2300` |
| 조회 가능 | 발표 후 약 10분 |
| 시간 필드 | `baseDate`, `baseTime`, `fcstDate`, `fcstTime` |
| 값 필드 | `fcstValue` |
| 반환 모델 | `list[ForecastItem]` |

대표 category:

| 코드 | 의미 | 단위/형식 |
|---|---|---|
| `TMP` | 1시간 기온 | C |
| `TMN` | 일 최저기온 | C |
| `TMX` | 일 최고기온 | C |
| `UUU` | 동서바람성분 | m/s |
| `VVV` | 남북바람성분 | m/s |
| `VEC` | 풍향 | deg |
| `WSD` | 풍속 | m/s |
| `SKY` | 하늘상태 | code |
| `PTY` | 강수형태 | code |
| `POP` | 강수확률 | % |
| `WAV` | 파고 | m |
| `PCP` | 1시간 강수량 | 숫자 또는 범주 문자열 |
| `SNO` | 1시간 신적설 | 숫자 또는 범주 문자열 |

### 4.4 `getFcstVersion`

예보 버전 정보를 조회합니다.

| 파라미터 | 설명 |
|---|---|
| `ftype` | 예보 타입 |
| `basedatetime` | 기준일시 문자열 |

초기 구현에서는 raw mapping을 반환합니다. 안정적인 사용례가 쌓이면 별도 모델을 추가할 수 있습니다.

## 5. 발표시각 선택

### 초단기실황

```python
cutoff = now_kst - timedelta(minutes=40)
base_time = cutoff.replace(minute=0, second=0, microsecond=0)
```

예시:

| 현재 KST | 선택 base |
|---|---|
| `2026-04-30 14:35` | `20260430 1300` |
| `2026-04-30 14:45` | `20260430 1400` |

### 초단기예보

```python
cutoff = now_kst - timedelta(minutes=15)
if cutoff.minute >= 30:
    base = HH30
else:
    base = previous_hour_HH30
```

예시:

| 현재 KST | 선택 base |
|---|---|
| `2026-04-30 14:44` | `20260430 1330` |
| `2026-04-30 14:50` | `20260430 1430` |

### 단기예보

발표시각 후보:

```python
[2, 5, 8, 11, 14, 17, 20, 23]
```

현재시각에서 10분을 뺀 뒤, 그 시각보다 작거나 같은 가장 최근 발표시각을 고릅니다. 후보가 없으면 전날 `23:00`을 사용합니다.

## 6. 좌표 변환

KMA 격자는 LCC DFS 좌표입니다.

라이브러리 public API에서는 외부 프로그램이 좌표계를 섞지 않도록 다음 값 객체를 제공합니다.

```python
from kma import GridPoint, LatLon, normalize_location
from kraddr.base import PlaceCoordinate

LatLon(37.5665, 126.9780).to_grid()  # GridPoint(nx=60, ny=127)
GridPoint(60, 127).to_latlon()       # 격자 중심에 가까운 WGS84 좌표
normalize_location(PlaceCoordinate(lat=37.5665, lon=126.9780))
normalize_location({"latitude": 37.5665, "longitude": 126.9780})
normalize_location({"nx": 60, "ny": 127})
```

- `LatLon`은 WGS84(`EPSG:4326`) 위도/경도입니다.
- `GridPoint`는 KMA DFS 격자 좌표입니다.
- `PlaceCoordinate`는 `kraddr.base` 공통 장소 좌표 DTO이며 public DTO에서는 `(lat, lon)` 순서입니다.
- `nx`/`ny`를 위도/경도로 해석하지 않습니다.
- `location=` 입력은 `lat/lon` 또는 `nx/ny`와 섞어 쓰지 않습니다.

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

| 위치 | WGS84 | nx, ny |
|---|---|---|
| 서울시청 | `37.5665, 126.9780` | `60, 127` |
| 부산시청 | `35.1796, 129.0756` | `98, 76` |
| 제주시청 | `33.4996, 126.5312` | `53, 38` |
| 강남역 | `37.4979, 127.0276` | `61, 125` |

## 7. 코드 매핑

코드 식별자는 외부 프로그램에서 문자열 오타를 줄일 수 있도록 public enum으로도 제공합니다.

```python
from kma import KmaEndpoint, WeatherCategory, label_for, unit_for

unit_for(WeatherCategory.TEMPERATURE)  # "C"
label_for(WeatherCategory.SKY, "1")    # "맑음"
label_for(WeatherCategory.PRECIPITATION_TYPE, "4", endpoint=KmaEndpoint.VILAGE_FCST)
```

`WeatherCategory`와 `KmaEndpoint`는 KMA wire value를 그대로 담은 `str` enum입니다. 알 수 없는 새 category는 모델에서 문자열 원문으로 보존합니다.

### `SKY`

| 코드 | 라벨 |
|---|---|
| `1` | 맑음 |
| `3` | 구름많음 |
| `4` | 흐림 |

### `PTY`: 초단기실황

| 코드 | 라벨 |
|---|---|
| `0` | 없음 |
| `1` | 비 |
| `2` | 비/눈 |
| `3` | 눈 |
| `5` | 빗방울 |
| `6` | 빗방울눈날림 |
| `7` | 눈날림 |

### `PTY`: 예보

| 코드 | 라벨 |
|---|---|
| `0` | 없음 |
| `1` | 비 |
| `2` | 비/눈 |
| `3` | 눈 |
| `4` | 소나기 |

## 8. 강수량/적설량 문자열

`PCP`, `SNO`는 숫자가 아닐 수 있습니다.

예시:

- `강수없음`
- `적설없음`
- `1.0mm 미만`
- `30.0~50.0mm`
- `50.0mm 이상`

라이브러리 정책:

- `ForecastItem.value`에는 원문 문자열을 보존합니다.
- `parse_amount()`는 대표값이 필요할 때만 사용합니다.
- 범위는 midpoint, 미만은 절반, 이상은 하한값을 반환합니다.

## 9. 응답 구조

정상 JSON 구조:

```json
{
  "response": {
    "header": {
      "resultCode": "00",
      "resultMsg": "NORMAL_SERVICE"
    },
    "body": {
      "items": {
        "item": []
      }
    }
  }
}
```

구현 규칙:

- `header.resultCode != "00"`이면 typed exception을 raise합니다.
- `items.item`이 dict 하나로 오면 list로 감쌉니다.
- `items.item`이 없거나 예상과 다르면 `KmaParseError`입니다.

## 10. Result code 처리

| 코드 | 의미 | 처리 |
|---|---|---|
| `00` | NORMAL_SERVICE | 성공 |
| `03` | NODATA_ERROR | `KmaRequestError` |
| `04` | HTTP_ERROR | `KmaServerError` |
| `12` | NO_OPENAPI_SERVICE_ERROR | `KmaRequestError` |
| `20` | SERVICE_ACCESS_DENIED_ERROR | `KmaAuthError` |
| `22` | LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR | `KmaRequestError` |
| `30` | SERVICE_KEY_IS_NOT_REGISTERED_ERROR | `KmaAuthError` |
| `31` | DEADLINE_HAS_EXPIRED_ERROR | `KmaAuthError` |
| `99` | UNKNOWN_ERROR | `KmaServerError` |

## 11. 구현 체크리스트

- [ ] `serviceKey`는 Decoding 키 기준으로 `params=`에 전달한다.
- [ ] `dataType=JSON`을 기본으로 보낸다.
- [ ] API별 base time helper를 사용한다.
- [ ] 모든 datetime은 KST aware로 만든다.
- [ ] `lat/lon`과 `nx/ny`를 동시에 받지 않는다.
- [ ] `PCP`/`SNO`를 무조건 float로 변환하지 않는다.
- [ ] `PTY` 매핑은 endpoint-aware로 처리한다.
- [ ] 실제 네트워크 호출 없는 단위 테스트를 먼저 작성한다.
