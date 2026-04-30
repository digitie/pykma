# Contributing

Thanks for helping improve `pykma`. This project wraps a fussy public API, so the best contributions are small, well-tested, and explicit about KMA edge cases.

## Local Setup

```bash
python -m venv .venv
pip install -e ".[dev]"
python -m pytest
```

The default test suite must not call the real KMA API.

## Before Changing Code

Read these files in order:

1. `AGENTS.md` for task ownership and verification expectations.
2. `kma-api.md` for endpoint behavior and KMA response quirks.
3. `docs/repeated-mistakes.md` for traps that already caused bugs or confusion.
4. `SKILL.md` for implementation invariants.

## Code Rules

- Keep public APIs stable unless the change is intentional and documented.
- Interpret naive `datetime` values as KST.
- Pass Decoding service keys through `requests` `params=`.
- Preserve `PCP` and `SNO` category strings in forecast items.
- Keep `PTY` mapping endpoint-aware.
- Convert non-`00` KMA result codes to typed exceptions.
- Add tests before or with behavior changes.

## Testing

Run:

```bash
python -m pytest
python -m compileall pykma tests
```

Optional checks:

```bash
ruff check .
mypy pykma
```

Live tests, when added, must be opt-in:

```bash
KMA_SERVICE_KEY=<decoded key> python -m pytest -m integration
```

Do not commit real service keys, raw URLs containing keys, or captured responses that include secrets.

## Documentation

Any change that affects user-facing behavior should update at least one of:

- `README.md` for usage and examples.
- `kma-api.md` for API details.
- `docs/troubleshooting.md` for symptoms and fixes.
- `docs/repeated-mistakes.md` when the change prevents a recurring issue.
- `CHANGELOG.md` for release-facing notes.

## Commit Style

Use short imperative commit messages, for example:

```text
Add endpoint-aware precipitation labels
```

Keep unrelated refactors out of feature or bugfix commits.

