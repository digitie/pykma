# AGENTS.md

## Role

This file is the operational guide for agents working on `pykma`. It is intentionally shorter than `SKILL.md`; use it to orient quickly, then read the more detailed documents for the task at hand.

## Instruction Priority

1. User request
2. This `AGENTS.md`
3. `kma-api.md`
4. `SKILL.md`
5. `README.md`
6. Existing code and tests
7. Minimal, reversible assumptions

If documents conflict, prefer the higher-priority source and update lower-priority docs when appropriate.

## Project Baseline

- `pykma` is a Python client for KMA public weather APIs.
- The first supported service is `VilageFcstInfoService_2.0`.
- The stable public endpoints are 초단기실황, 초단기예보, 단기예보, and 예보버전.
- Python support starts at 3.9.
- Runtime dependency is `requests`.
- Default tests must run without real KMA network calls.

## Documentation Layout

- `README.md`: user-facing overview, install, examples, model summary.
- `kma-api.md`: endpoint details, KMA quirks, base-time rules, category codes.
- `SKILL.md`: implementation invariants and detailed rules for agents.
- `AGENTS.md`: task routing, ownership, and verification checklist.
- `docs/repeated-mistakes.md`: mistakes that have already happened or are likely to recur.
- `docs/testing.md`: test design, live-test constraints, and regression workflow.
- `docs/troubleshooting.md`: symptom-to-fix guide for user and maintainer issues.
- `CONTRIBUTING.md`: contributor setup and workflow.
- `CHANGELOG.md`: release-facing changes.
- `pyproject.toml`: packaging, dependencies, lint/test config.

## Module Map

- `pykma/client.py`: `KmaClient`, endpoint methods, response parsing.
- `pykma/_http.py`: session construction and retry setup.
- `pykma/grid.py`: LCC DFS grid conversion.
- `pykma/time_utils.py`: KST-aware base date/time selection.
- `pykma/codes.py`: category maps, labels, unit hints, precipitation parsing.
- `pykma/models.py`: frozen dataclasses returned to users.
- `pykma/exceptions.py`: exception hierarchy.
- `pykma/cli.py`: JSON CLI entrypoint.
- `tests/`: network-free unit tests.

## Non-Negotiables

- Do not print, log, commit, or fixture real service keys.
- Do not perform real API calls in default tests.
- Do not treat `nx`/`ny` as latitude/longitude.
- Do not use naive local timezone assumptions; KMA times are KST.
- Do not convert `PCP` and `SNO` range labels blindly to floats.
- Do not return silent empty lists for KMA result-code failures.
- Do not change public method names casually.

## Agent Ownership Map

### Client Agent

Owns:

- `pykma/client.py`
- `pykma/_http.py`
- request/response parsing
- error mapping

Checklist:

- service key goes through `serviceKey`
- `dataType=JSON`
- `pageNo` and `numOfRows` defaults are present
- fake-session tests cover request params
- non-`00` result codes raise typed exceptions

### Time Agent

Owns:

- `pykma/time_utils.py`
- base time tests

Checklist:

- `getUltraSrtNcst`: `HH00`, available after 40 minutes
- `getUltraSrtFcst`: `HH30`, available after 15 minutes
- `getVilageFcst`: `0200/0500/0800/1100/1400/1700/2000/2300`, available after 10 minutes
- previous-day midnight cases are tested

### Grid Agent

Owns:

- `pykma/grid.py`
- grid conversion tests

Checklist:

- official LCC DFS constants are unchanged
- Seoul, Busan, Jeju, Gangnam verification points pass
- reverse conversion uses tolerant assertions

### Codes Agent

Owns:

- `pykma/codes.py`
- category label tests

Checklist:

- `SKY` maps only `1`, `3`, `4`
- `PTY` is endpoint-aware
- `PCP` and `SNO` labels are preserved
- `parse_amount()` handles no-rain, less-than, range, and greater-than labels

### Docs Agent

Owns:

- `README.md`
- `kma-api.md`
- `SKILL.md`
- `AGENTS.md`

Checklist:

- user examples match actual public API
- docs mention Decoding key with `params=`
- docs include KST time behavior
- docs distinguish observed vs forecast `PTY`
- docs do not claim live values are stable

### Release Agent

Owns:

- `pyproject.toml`
- packaging metadata
- changelog/release notes when added

Checklist:

- version bump is intentional
- Python requirement matches syntax used by code and tests
- package data includes `py.typed`
- `pytest`, `ruff check .`, and `mypy pykma` are considered before release

## Verification

Fast local checks:

```bash
python -m compileall pykma tests
python -m pytest
```

Optional quality checks:

```bash
ruff check .
mypy pykma
```

Live checks, when introduced, must be opt-in:

```bash
KMA_SERVICE_KEY=<decoded service key> python -m pytest -m integration
```

## Current Notes

- The initial project skeleton and docs were derived from `README.md`, `SKILL.md`, and the structure of the sibling `pyopinet` project.
- `kma-api.md` is the preferred place for detailed API quirks so `README.md` can stay readable.
- `docs/repeated-mistakes.md` must be updated when a bug reflects a known KMA/API trap.
- `docs/testing.md` must stay aligned with test markers and test file layout.
- `docs/troubleshooting.md` should get a new entry when a user-facing failure mode is discovered.
- If expanding beyond `VilageFcstInfoService_2.0`, keep the original client stable and add clearly named modules for new services.
