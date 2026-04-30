---
name: kma-api-python-builder
description: Use this skill when building, extending, debugging, or testing a Python client for the Korean Meteorological Administration public weather APIs. Trigger on KMA, 기상청, 단기예보, 초단기실황, 초단기예보, 동네예보, VilageFcstInfoService_2.0, nx/ny grid conversion, base_time calculation, serviceKey encoding, SKY/PTY codes, or apis.data.go.kr/1360000 URLs.
---

# KMA Python Library Builder

You are helping build and maintain `pykma`, a Python client for KMA public weather APIs. Read `README.md`, `kma-api.md`, and `AGENTS.md` before changing public behavior.

## Project Invariants

1. **Primary service**: `VilageFcstInfoService_2.0`.
2. **Base URL**: `http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0`.
3. **Auth parameter**: `serviceKey`.
4. **Recommended key form**: Decoding key when using `requests` `params=`.
5. **Output format**: always request `dataType=JSON` for user-facing methods.
6. **Timezone**: KMA forecast times are KST(UTC+9). Naive datetimes are interpreted as KST.
7. **Coordinates**: public API accepts WGS84 `lat`/`lon` or KMA grid `nx`/`ny`; never treat `nx`/`ny` as latitude/longitude.
8. **No silent empty success**: non-`00` KMA result codes must surface as typed exceptions.
9. **Offline tests by default**: normal test runs must not call the real KMA API.
10. **Gateway separation**: data.go.kr uses `serviceKey`; APIHub uses `authKey`.

## Supported Endpoints

Start with these endpoints:

| Public method | Endpoint | Purpose |
|---|---|---|
| `KmaClient.now()` | `getUltraSrtNcst` | 초단기실황 |
| `KmaClient.forecast_short()` | `getUltraSrtFcst` | 초단기예보 |
| `KmaClient.forecast()` | `getVilageFcst` | 단기예보 |
| `KmaClient.version()` | `getFcstVersion` | 예보 버전 |

Other KMA services such as 중기예보, 기상특보, AWS 관측, or APIHub datasets must be added as separate modules or explicitly scoped extensions.

## Required Deliverables When Implementing From Scratch

```text
pykma/
├── __init__.py          # re-export public client, models, exceptions, coordinate helpers
├── client.py            # KmaClient
├── grid.py              # to_grid, to_latlon using KMA LCC DFS formula
├── time_utils.py        # KST-aware latest base time helpers
├── codes.py             # SKY/PTY maps, category units, parse_amount
├── models.py            # frozen dataclasses
├── exceptions.py        # KmaError hierarchy
├── _http.py             # requests session and retry setup
└── cli.py               # console entrypoint
tests/
├── test_client.py
├── test_codes.py
├── test_grid.py
└── test_time_utils.py
pyproject.toml
README.md
kma-api.md
AGENTS.md
```

## Public API Rules

### `KmaClient`

```python
KmaClient(service_key, *, timeout=10, retries=3, base_url=None, session=None)
KmaClient.from_env(name="KMA_SERVICE_KEY")
```

Every location-aware method accepts exactly one coordinate mode:

```python
kma.now(lat=37.5665, lon=126.9780)
kma.now(nx=60, ny=127)
```

Reject mixed or partial coordinates:

- `lat` without `lon`: `ValueError`
- `nx` without `ny`: `ValueError`
- both `lat/lon` and `nx/ny`: `ValueError`

## Type Conversion Policy

KMA responses are string-heavy. Convert at the model boundary, but preserve semantically important labels.

| Source field/value | Python surface | Rule |
|---|---|---|
| `baseDate` + `baseTime` | aware `datetime` | KST timezone |
| `fcstDate` + `fcstTime` | aware `datetime` | KST timezone |
| numeric categories | `float` | use `float()` when safe |
| humidity/wind direction in snapshot | `int | None` | parse via float then int |
| `SKY` | raw value plus label | `1`, `3`, `4` only |
| `PTY` | raw value plus endpoint-aware label | observed and forecast maps differ |
| `PCP`, `SNO` | `str` | preserve range/category labels |
| `RN1` in current observation | `float | None` | use `parse_amount()` |
| malformed numeric values | raw string or `None` by field | do not crash during optional parsing |

### Do Not Blindly Float These Values

`PCP` and `SNO` can be category strings:

- `강수없음`
- `적설없음`
- `1.0mm 미만`
- `30.0~50.0mm`
- `50.0mm 이상`

Keep these as strings in `ForecastItem.value`. Provide `parse_amount()` for callers who want representative numeric values.

## Time Rules

### `getUltraSrtNcst`

- Published every hour at `HH00`.
- Usually available after 40 minutes.
- At KST `14:35`, use `13:00`.
- At KST `14:45`, use `14:00`.

### `getUltraSrtFcst`

- Published every hour at `HH30`.
- Usually available after 15 minutes, so `HH45`.
- At KST `14:44`, use `13:30`.
- At KST `14:50`, use `14:30`.

### `getVilageFcst`

- Published at `0200`, `0500`, `0800`, `1100`, `1400`, `1700`, `2000`, `2300`.
- Usually available after 10 minutes.
- Before `02:10`, use previous day `2300`.

All helpers belong in `pykma/time_utils.py` and must have midnight/previous-day tests.

## Grid Conversion Rules

KMA uses Lambert Conformal Conic DFS grid coordinates.

Constants:

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

Verification points:

| Location | WGS84 | KMA grid |
|---|---|---|
| Seoul City Hall | `(37.5665, 126.9780)` | `(60, 127)` |
| Busan City Hall | `(35.1796, 129.0756)` | `(98, 76)` |
| Jeju City Hall | `(33.4996, 126.5312)` | `(53, 38)` |
| Gangnam Station | `(37.4979, 127.0276)` | `(61, 125)` |

Do not change constants unless there is a source-backed reason and test fixtures are updated.

## Code Mapping Rules

### `SKY`

```python
{"1": "맑음", "3": "구름많음", "4": "흐림"}
```

Do not invent `2`.

### `PTY`

Observed current conditions (`getUltraSrtNcst`):

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

Forecasts (`getUltraSrtFcst`, `getVilageFcst`):

```python
{
    "0": "없음",
    "1": "비",
    "2": "비/눈",
    "3": "눈",
    "4": "소나기",
}
```

Mapping must be endpoint-aware.

## Exception Hierarchy

```text
KmaError
├── KmaAuthError
├── KmaRequestError
├── KmaServerError
└── KmaParseError
```

Result-code mapping:

| Code | Handling |
|---|---|
| `00` | success |
| `03` | `KmaRequestError` |
| `04` | `KmaServerError` |
| `12` | `KmaRequestError` |
| `20` | `KmaAuthError` |
| `22` | `KmaRequestError` |
| `30` | `KmaAuthError` |
| `31` | `KmaAuthError` |
| `99` | `KmaServerError` |

Malformed JSON or unexpected response structure raises `KmaParseError`.

## HTTP Layer Rules

- Use one place for session and retry setup: `pykma/_http.py`.
- Retry only transient GET failures such as `429`, `500`, `502`, `503`, `504`.
- Do not retry authentication failures.
- Do not log or print service keys.
- Keep `http://` as the default base URL unless docs/tests intentionally change it.
- Allow dependency injection via `session=` for tests.

## Docstring Rules

Every public method should document:

- endpoint name
- coordinate mode
- time selection behavior
- return type
- exceptions that commonly occur

## Testing Rules

Required offline tests:

- grid conversion known points
- grid reverse conversion tolerance
- latest base time helpers, including midnight
- `SKY`/`PTY` endpoint-aware labels
- `PCP`/`SNO` preservation
- `parse_amount()` ranges
- `KmaClient` request param shape with fake session
- result-code exception mapping

Optional live tests:

- must be marked `integration` or `live`
- must require `KMA_SERVICE_KEY`
- must skip cleanly when the key is absent
- must not assert unstable weather values, only response shape and types

## Common Pitfalls

1. Passing an already encoded service key through `params=` can double-encode it and trigger `SERVICE_KEY_IS_NOT_REGISTERED_ERROR`.
2. Using the current clock time directly as `base_time` often returns empty data.
3. Treating `nx`/`ny` as WGS84 coordinates is incorrect.
4. Calling `float()` on `PCP`/`SNO` can fail because they are often Korean range labels.
5. Assuming `PTY=4` means the same thing in all endpoints is wrong.
6. Returning raw API dictionaries directly leaks KMA quirks into user code.
7. Trusting mojibake in PowerShell as proof that UTF-8 files are broken can lead to unnecessary churn. Verify Korean text with Python UTF-8 reads or assertions.

When one of these mistakes is fixed, update `docs/repeated-mistakes.md` with the symptom, rule, and guardrail test.

## Documentation Update Rules

- Update `README.md` for user-facing API changes.
- Update `kma-api.md` for endpoint details, response fields, or KMA behavior.
- Update `docs/apihub.md` for APIHub categories, discovery, or response-format behavior.
- Update `docs/datagokr.md` for generic data.go.kr service support.
- Update `docs/testing.md` when test strategy, markers, or fixture policy changes.
- Update `docs/troubleshooting.md` when a user-visible error gets a known fix.
- Update `docs/repeated-mistakes.md` when a recurring trap is discovered or prevented.
- Update `CHANGELOG.md` for release-facing additions, fixes, and breaking changes.

## When Adding A New Endpoint

1. Add a concise section to `kma-api.md`.
2. Add or update models only if the shape is stable.
3. Add mock response tests before live tests.
4. Keep the public method name Pythonic and endpoint-agnostic where possible.
5. Preserve raw response fields in `raw` only when useful for debugging.
