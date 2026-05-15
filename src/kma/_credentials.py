"""API 인증값 입력 정규화와 로컬 환경 파일 로더."""

from __future__ import annotations

import os
from pathlib import Path

DATA_GOKR_ENV_NAMES = ("DATA_GOKR_SERVICE_KEY", "KMA_SERVICE_KEY")
APIHUB_ENV_NAMES = ("KMA_APIHUB_AUTH_KEY", "KMA_APIHUB_KEY")
DEFAULT_ENV_FILES = (".env", ".env.local")


def normalize_api_key(value: str, *, field_name: str) -> str:
    """복사/붙여넣기로 섞인 공백을 제거한 API 인증값을 반환합니다."""

    normalized = "".join(str(value).split())
    if not normalized:
        raise ValueError(f"{field_name} is required")
    return normalized


def api_key_for_gateway(gateway: str) -> str:
    """gateway 이름에 맞는 로컬 API 인증값을 환경변수 또는 `.env`에서 읽습니다."""

    names = env_names_for_gateway(gateway)
    key = first_env_value(names)
    return normalize_api_key(key, field_name="/".join(names))


def env_names_for_gateway(gateway: str) -> tuple[str, ...]:
    """gateway별로 확인할 환경변수 이름을 반환합니다."""

    normalized = gateway.strip().lower()
    if normalized == "datagokr":
        return DATA_GOKR_ENV_NAMES
    if normalized == "apihub":
        return APIHUB_ENV_NAMES
    raise ValueError(f"unknown gateway: {gateway}")


def first_env_value(names: tuple[str, ...] | list[str]) -> str:
    """process env와 로컬 env 파일에서 첫 번째로 발견한 값을 반환합니다."""

    for name in _unique_names(names):
        value = os.getenv(name)
        if value is not None and value.strip():
            return value

    local_env = load_local_env()
    for name in _unique_names(names):
        value = local_env.get(name)
        if value is not None and value.strip():
            return value
    raise ValueError(f"{' or '.join(_unique_names(names))} is not set")


def load_local_env(
    *,
    start: str | Path | None = None,
    filenames: tuple[str, ...] = DEFAULT_ENV_FILES,
) -> dict[str, str]:
    """현재 작업 디렉터리의 `.env`와 `.env.local` 값을 읽어 반환합니다.

    실제 process env는 수정하지 않습니다. 같은 key가 여러 파일에 있으면 가까운
    디렉터리의 파일이 우선하고, 같은 디렉터리에서는 기본값 기준 `.env.local`
    값이 `.env`보다 우선합니다.
    """

    env: dict[str, str] = {}
    for directory in _candidate_env_dirs(start or Path.cwd()):
        for filename in filenames:
            path = directory / filename
            if path.is_file():
                env.update(_parse_env_file(path))
    return env


def _candidate_env_dirs(start: str | Path) -> tuple[Path, ...]:
    path = Path(start).resolve()
    if path.is_file():
        path = path.parent
    return tuple(reversed((path, *path.parents)))


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        clean_key = key.strip()
        if not clean_key or clean_key.startswith("#"):
            continue
        values[clean_key] = _clean_env_value(value)
    return values


def _clean_env_value(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        return text[1:-1]
    if " #" in text:
        text = text.split(" #", 1)[0].rstrip()
    return text


def _unique_names(names: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for name in names:
        if name and name not in seen:
            seen.add(name)
            ordered.append(name)
    return tuple(ordered)
