# Testing Guide

`pykma` tests are designed to catch KMA-specific mistakes without depending on live weather data.

## Default Suite

```bash
python -m pytest
```

Default tests must be:

- offline
- deterministic
- safe to run without `KMA_SERVICE_KEY`
- focused on request parameters, parsing, conversion, and exception behavior

## Current Coverage Areas

- `tests/test_client.py`: request parameters, fake-session response parsing, result-code mapping, malformed response handling.
- `tests/test_codes.py`: `SKY`/`PTY` labels, `PCP`/`SNO` preservation, `parse_amount()`.
- `tests/test_grid.py`: known grid conversion points and bounds.
- `tests/test_time_utils.py`: KST conversion and endpoint-specific base time selection.
- `tests/test_cli.py`: CLI argument handling and JSON output shape.
- `tests/test_datagokr.py`: generic data.go.kr service/operation calls and envelope handling.
- `tests/test_apihub.py`: APIHub generic request, `typ02/openApi` helper, and discovery HTML parsers.

## Live Tests

Live tests are allowed only when they are explicitly marked:

```python
import os
import pytest

pytestmark = pytest.mark.integration

@pytest.mark.skipif(not os.getenv("KMA_SERVICE_KEY"), reason="KMA_SERVICE_KEY is not set")
def test_live_now_shape():
    ...
```

Live tests should assert shape and types, not exact weather values.

Good assertions:

- response is not empty for a well-known grid
- datetime fields are KST-aware
- `nx` and `ny` match the request
- categories are strings

Bad assertions:

- exact temperature
- exact sky or precipitation labels
- exact number of forecast rows unless the API contract guarantees it

## Manual Smoke Tests

With a Decoding key:

```bash
KMA_SERVICE_KEY=<decoded key> pykma now --nx 60 --ny 127
KMA_SERVICE_KEY=<decoded key> pykma forecast --lat 37.5665 --lon 126.9780
```

PowerShell:

```powershell
$env:KMA_SERVICE_KEY="<decoded key>"
pykma now --nx 60 --ny 127
```

## Regression Rule

When a bug is fixed:

1. Add a failing test that would have caught it.
2. Fix the code.
3. Update `docs/repeated-mistakes.md` if the bug fits a recurring KMA trap.
