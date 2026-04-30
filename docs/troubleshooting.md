# Troubleshooting

This guide maps common symptoms to likely causes.

## `SERVICE_KEY_IS_NOT_REGISTERED_ERROR`

Likely causes:

- The key is expired or not approved for `VilageFcstInfoService_2.0`.
- An Encoding key was passed through `requests` `params=`, causing double encoding.
- The service application is approved for a different KMA service.

Fix:

- Use the Decoding key in `KMA_SERVICE_KEY`.
- Confirm the data.go.kr application status.
- Try a minimal request with `KmaClient.now(nx=60, ny=127)`.

## Empty Forecast Items Or `NODATA_ERROR`

Likely causes:

- The requested `base_time` is too recent.
- The endpoint release schedule was ignored.
- The grid coordinates are out of range or point somewhere unintended.

Fix:

- Let `KmaClient` choose `base_time` by omitting manual date/time params.
- Verify the location with `to_grid(lat, lon)`.
- See `kma-api.md` for endpoint-specific release delays.

## Korean Labels Look Broken In PowerShell

Likely cause:

- Terminal code page rendering, not necessarily file corruption.

Fix:

- Verify using Python UTF-8 reads or tests.

```bash
python -c "from pykma.codes import label_for; print(repr(label_for('SKY', '1')))"
```

Expected value:

```text
'맑음'
```

## `ValueError` When Parsing `PCP` Or `SNO`

Likely cause:

- Code tried `float(value)` on a Korean range label.

Fix:

- Keep `ForecastItem.value` as returned by the library.
- Use `parse_amount()` only when a representative number is acceptable.

```python
from pykma.codes import parse_amount

parse_amount("1.0mm 미만")    # 0.5
parse_amount("30.0~50.0mm")  # 40.0
```

## Wrong Precipitation Label

Likely cause:

- `PTY` was mapped without considering the endpoint.

Fix:

- Pass the endpoint to `label_for()`.
- Use `KmaClient` model output instead of mapping manually where possible.

## CLI Reports Missing Coordinates

Examples:

```bash
pykma now --lat 37.5665
pykma now --nx 60
```

Fix:

Use complete coordinate pairs:

```bash
pykma now --lat 37.5665 --lon 126.9780
pykma now --nx 60 --ny 127
```

Do not mix coordinate systems:

```bash
pykma now --lat 37.5665 --lon 126.9780 --nx 60 --ny 127
```

## Import Works But Network Calls Fail With Missing `requests`

`pykma` keeps coordinate helpers importable even in minimal environments, but `KmaClient` network calls require `requests`.

Fix:

```bash
pip install -e .
```

or:

```bash
pip install requests
```

## APIHub Call Returns Text Instead Of JSON

Likely cause:

- Many APIHub endpoints are old text, CSV-like text, image, or binary endpoints.

Fix:

- Use `ApiHubResponse.text` for text endpoints.
- Use `ApiHubResponse.content` for image or file endpoints.
- Call `ApiHubResponse.json()` only when the endpoint documentation says it returns JSON.

## `authKey` Works On APIHub But `serviceKey` Does Not

APIHub and data.go.kr are separate gateways.

- APIHub uses `authKey`.
- data.go.kr uses `serviceKey`.

Use `ApiHubClient` for `https://apihub.kma.go.kr/api/...` paths and `DataGoKrClient` or `KmaClient` for `http://apis.data.go.kr/1360000/...` paths.
