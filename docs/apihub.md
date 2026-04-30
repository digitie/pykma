# KMA APIHub Support

`apihub.kma.go.kr` is separate from `data.go.kr`.

| Portal | Auth parameter | Typical response |
|---|---|---|
| data.go.kr KMA gateway | `serviceKey` | JSON/XML REST envelope |
| KMA APIHub | `authKey` | text, CSV-like text, JSON, XML, image, binary file |

Because APIHub mixes many response formats, `pykma` supports it through a generic client instead of pretending all endpoints share one model.

Primary official sources checked:

- https://apihub.kma.go.kr/apiInfo.do
- https://apihub.kma.go.kr/apiList.do
- https://apihub.kma.go.kr/specialApiList.do

## Official Category Coverage

The APIHub introduction page lists these categories:

| id | category | examples |
|---|---|---|
| 2 | 지상관측 | ASOS, AWS, 기후통계, 황사관측, 지점정보 |
| 3 | 해양관측 | 해양기상부이, 등표, 기상1호 |
| 4 | 고층관측 | 레윈존데, 연직바람, 고층 지점정보 |
| 5 | 레이더 | 강수량, 원시자료, 낙뢰, 지점정보 |
| 6 | 위성 | 천리안 2A호, 천리안 1호 |
| 7 | 지진/화산 | 지진정보, 지진해일, 화산정보 |
| 8 | 태풍 | 태풍정보, TD, 베스트트랙 |
| 9 | 수치모델 | 수치예보모델, 초단기예측, 그래픽, 분석일기도 |
| 10 | 예특보 | 단기예보, 중기예보, 기상특보, 영향예보, 구역정보 |
| 11 | 융합기상 | 관광, 농업, 해수욕장, 전력, 산악, 도로위험 |
| 12 | 세계기상 | GTS, GTS 지점정보, NCEI |
| 13 | 산업특화 | 에너지, 수자원, 농업, 교통 |
| 14 | 항공기상 | METAR, AMOS, 공항예특보, AMDAR, 저고도 |
| 15 | 기후변화 | 기후변화시나리오, 기후통계 |

On 2026-05-01, the APIHub pages exposed 59 services through `const apiList = [...]`. Of those, 50 service pages exposed generated sample URLs in the HTML, totaling 464 unique path/parameter signatures. Some 융합기상/기후변화 pages are linked services or require interaction beyond the static sample URL pattern, so `pykma` treats discovery as live portal metadata rather than a frozen complete contract.

## Generic Client

```python
from pykma import ApiHubClient

hub = ApiHubClient.from_env()  # KMA_APIHUB_AUTH_KEY or KMA_APIHUB_KEY

response = hub.request_path(
    "/api/typ01/url/kma_sfctm2.php",
    {"tm": "202211300900", "stn": "108", "help": "1"},
)
print(response.text)
```

The client always appends `authKey`.

```python
hub.request_path("/api/typ01/url/wrn_reg.php", {"tmfc": "0"})
```

Full URLs copied from APIHub are accepted if the path starts with `/api/`; embedded sample `authKey` values are not reused.

## Typ02 OpenAPI Helper

Many APIHub endpoints use:

```text
/api/typ02/openApi/{service}/{operation}
```

Use `open_api()` for those.

```python
response = hub.open_api(
    "MidFcstInfoService",
    "getMidFcst",
    {"stnId": "108", "tmFc": "202605010600"},
)
data = response.json()
```

Defaults:

- `pageNo=1`
- `numOfRows=10`
- `dataType=JSON`

## Discovery

`discover_services()` fetches APIHub service lists for official category ids.

```python
services = hub.discover_services()
for service in services:
    print(service.category_id, service.category_name, service.service_id, service.service_name)
```

`discover_endpoints()` fetches generated sample URLs for a service page and extracts:

- path
- parameter names
- sample parameter values, excluding `authKey`

```python
endpoints = hub.discover_endpoints(category_id=10, service_id=288)
for endpoint in endpoints:
    print(endpoint.path, endpoint.parameters)
```

## CLI

```bash
pykma apihub /api/typ01/url/kma_sfctm2.php \
  --param tm=202211300900 \
  --param stn=108 \
  --param help=1
```

PowerShell:

```powershell
$env:KMA_APIHUB_AUTH_KEY="<APIHub authKey>"
pykma apihub /api/typ01/url/wrn_reg.php --param tmfc=0
```

## Why Not A Dataclass For Every Endpoint?

APIHub includes:

- text tables
- CSV-like text
- JSON REST envelopes
- XML
- image URLs and image bytes
- GRIB/NetCDF/file downloads
- interactive map-rendering endpoints

Forcing those into one dataclass style would hide important endpoint differences. The library therefore provides:

- specialized dataclasses for stable data.go.kr 단기예보
- generic APIHub response objects for broad endpoint coverage
- discovery helpers so new APIHub pages can be inspected without a package release

## Implementation Guardrails

- Never log or commit `authKey`.
- Do not assume UTF-8-only payloads for old text endpoints.
- Do not assume every APIHub endpoint returns JSON.
- Do not retry or parse binary/image endpoints as text beyond exposing `content`.
- Keep discovery tests offline by using captured HTML snippets, not live portal calls.
