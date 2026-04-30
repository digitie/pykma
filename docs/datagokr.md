# data.go.kr KMA Support

`pykma.KmaClient` remains the typed, friendly client for the high-use 단기예보 service. For other KMA public-data services on `apis.data.go.kr/1360000`, use `DataGoKrClient`.

Primary official sources checked:

- https://www.data.go.kr/data/15084084/openapi.do
- https://www.data.go.kr/data/15059468/openapi.do
- https://www.data.go.kr/data/15000415/openapi.do
- https://www.data.go.kr/tcs/dss/selectApiDataDetailView.do?publicDataPk=15059093
- APIHub redirect/link records on data.go.kr for model, satellite, aviation, warning, and other newer KMA APIs.

## Typed Client

```python
from pykma import KmaClient

kma = KmaClient.from_env()
kma.now(nx=60, ny=127)
kma.forecast_short(nx=60, ny=127)
kma.forecast(nx=60, ny=127)
```

This client covers:

- `VilageFcstInfoService_2.0/getUltraSrtNcst`
- `VilageFcstInfoService_2.0/getUltraSrtFcst`
- `VilageFcstInfoService_2.0/getVilageFcst`
- `VilageFcstInfoService_2.0/getFcstVersion`

## Generic Client

```python
from pykma import DataGoKrClient

client = DataGoKrClient.from_env()
body = client.request(
    "MidFcstInfoService",
    "getMidFcst",
    {"stnId": "108", "tmFc": "202605010600"},
)
```

For operations with the standard `response.body.items.item` shape:

```python
items = client.items(
    "MidFcstInfoService",
    "getMidFcst",
    {"stnId": "108", "tmFc": "202605010600"},
)
```

Defaults:

- `serviceKey=<KMA_SERVICE_KEY>`
- `pageNo=1`
- `numOfRows=10`
- `dataType=JSON`

## Examples From data.go.kr Search

Official data.go.kr pages show these KMA REST services among others:

| service | operation example | notes |
|---|---|---|
| `VilageFcstInfoService_2.0` | `getUltraSrtNcst`, `getVilageFcst` | typed by `KmaClient` |
| `MidFcstInfoService` | `getMidFcst`, `getMidTa`, `getMidLandFcst`, `getMidSeaFcst` | generic JSON/XML envelope |
| `WthrWrnInfoService` | `getWthrWrnList` | 기상특보 |
| `AsosDalyInfoService` | `getWthrDataList` | ASOS 일자료 |
| `YdstInfoService` | `getYdstSatlitImg`, `getYdstObs` | 황사정보 |
| `LgtDistrbInfoService` | `getLgtDistrb` | 낙뢰분포도 |
| `CloudSatlitInfoService` | `getGk2acldAll` and related | 위성자료 경량화 |
| `UppInfoService` | varies by guide | 고층기상관측 |

Some newer data.go.kr entries are LINK-type records that redirect to APIHub rather than using the old `serviceKey` gateway. Use `ApiHubClient` for those.

## Auth Key Rule

Use the Decoding service key when calling through `requests params=`.

```python
DataGoKrClient(service_key="decoded-key")
```

If you paste an already encoded key into `params=`, it may be encoded again and fail as `SERVICE_KEY_IS_NOT_REGISTERED_ERROR`.
