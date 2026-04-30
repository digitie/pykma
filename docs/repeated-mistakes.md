# Repeated Mistakes To Avoid

This document records mistakes that are easy to repeat while building `pykma`. When one of these shows up in code review or debugging, add a test and update this file.

## Service Key Encoding

**Mistake:** Passing an already URL-encoded service key through `requests` `params=`.

**Symptom:** KMA returns `SERVICE_KEY_IS_NOT_REGISTERED_ERROR` even though the key looks correct.

**Rule:** The library path uses `params=`, so examples and tests assume the Decoding key. Use an Encoding key only when manually constructing a full URL string.

**Guardrail:** Client tests assert that `serviceKey` is passed as a normal request parameter.

## Base Time Is Not Current Time

**Mistake:** Setting `base_time` to the current clock hour or minute.

**Symptom:** Empty `items`, `NODATA_ERROR`, or unstable tests around release boundaries.

**Rule:** Always use helpers in `pykma/time_utils.py`.

| Endpoint | Correct helper |
|---|---|
| `getUltraSrtNcst` | `latest_ultra_srt_ncst_base()` |
| `getUltraSrtFcst` | `latest_ultra_srt_fcst_base()` |
| `getVilageFcst` | `latest_vilage_base()` |

**Guardrail:** Time tests cover release lag, previous-day behavior, naive KST interpretation, and UTC conversion.

## `nx`/`ny` Are Not Latitude/Longitude

**Mistake:** Passing latitude/longitude into `nx`/`ny` or treating grid values as geographic degrees.

**Symptom:** Forecasts for the wrong location or request parameter validation errors.

**Rule:** Use `lat`/`lon` for WGS84 and `nx`/`ny` only for KMA DFS grid coordinates.

**Guardrail:** `pykma/grid.py` validates WGS84 bounds and official grid bounds. Client tests reject mixed and partial coordinate modes.

## `PCP` And `SNO` Are Not Always Numbers

**Mistake:** Calling `float()` on every forecast value.

**Symptom:** `ValueError` on labels such as `1.0mm 미만`, `강수없음`, or `30.0~50.0mm`.

**Rule:** Preserve `PCP` and `SNO` strings in `ForecastItem.value`. Use `parse_amount()` only when a representative number is explicitly needed.

**Guardrail:** Code tests ensure `PCP` and `SNO` labels remain strings and `parse_amount()` handles common Korean range labels.

## `PTY` Codes Differ By Endpoint

**Mistake:** Using one precipitation-type table for all endpoints.

**Symptom:** `PTY=4` is incorrectly interpreted for 초단기실황, or `PTY=5` is incorrectly interpreted for forecast endpoints.

**Rule:** Use endpoint-aware mapping:

- `getUltraSrtNcst`: `0`, `1`, `2`, `3`, `5`, `6`, `7`
- `getUltraSrtFcst` / `getVilageFcst`: `0`, `1`, `2`, `3`, `4`

**Guardrail:** Label tests assert endpoint-specific `PTY` behavior.

## Do Not Let KMA Shape Drift Leak Out

**Mistake:** Letting `KeyError`, `TypeError`, raw dicts, or silent empty success escape from parser code.

**Symptom:** Users see inconsistent exceptions or have to understand KMA's nested `response.header.body.items.item` shape.

**Rule:** Convert malformed envelopes/items into `KmaParseError`; convert non-`00` result codes into typed KMA exceptions.

**Guardrail:** Client tests cover malformed envelopes, missing `items`, malformed forecast items, single-item dict responses, and result-code mapping.

## Korean Text Must Stay UTF-8

**Mistake:** Trusting terminal rendering when PowerShell displays mojibake.

**Symptom:** Korean labels appear broken in terminal output, but the file may still be valid UTF-8.

**Rule:** Verify with Python `Path(...).read_text(encoding="utf-8")` or tests that compare real Korean strings.

**Guardrail:** Tests assert actual labels such as `맑음`, `소나기`, `빗방울`, and `강수없음`.

## APIHub Is Not data.go.kr

**Mistake:** Sending `serviceKey` to APIHub or `authKey` to data.go.kr.

**Symptom:** Authentication failures even though the key is valid on the other portal.

**Rule:** `ApiHubClient` appends `authKey`; `DataGoKrClient` and `KmaClient` send `serviceKey`.

**Guardrail:** Tests assert both generic clients build the correct auth parameter.

## APIHub Does Not Always Return JSON

**Mistake:** Calling `.json()` or forcing dataclass parsing for every APIHub endpoint.

**Symptom:** parse errors on text tables, image endpoints, or file downloads.

**Rule:** `ApiHubClient` returns `ApiHubResponse` with `text` and `content`. Parse per endpoint.

**Guardrail:** APIHub tests use text responses and only call `json()` in a JSON-specific test.
