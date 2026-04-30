# Changelog

All notable changes to `pykma` will be documented here.

## 0.1.0 - Unreleased

### Added

- Initial `KmaClient` for `getUltraSrtNcst`, `getUltraSrtFcst`, `getVilageFcst`, and `getFcstVersion`.
- KMA LCC DFS grid conversion helpers: `to_grid()` and `to_latlon()`.
- KST-aware base time helpers for 초단기실황, 초단기예보, and 단기예보.
- Endpoint-aware `SKY` and `PTY` label mapping.
- Safe `PCP` and `SNO` handling that preserves Korean range labels.
- Typed exception hierarchy for auth, request, server, and parse errors.
- JSON CLI entrypoint.
- Offline unit tests covering client parsing, time rules, coordinate conversion, code mapping, and CLI behavior.
- Documentation set: README, API reference, agent guide, troubleshooting, testing, and repeated-mistake notes.

