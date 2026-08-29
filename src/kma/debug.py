"""디버그 UI와 fixture 저장에 공통으로 쓰는 보조 기능."""

from __future__ import annotations

import json
import re
import traceback as _traceback
from collections.abc import Mapping
from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime
from os import PathLike
from pathlib import Path
from typing import Any, cast
from zoneinfo import ZoneInfo

from pydantic import BaseModel

from .exceptions import KmaError
from .metadata import redact_credentials_in_text

SENSITIVE_KEYS = {
    "authorization",
    "x-api-key",
    "api_key",
    "apikey",
    "api-key",
    "auth_key",
    "authkey",
    "auth-key",
    "service_key",
    "servicekey",
    "service-key",
    "access_token",
    "refresh_token",
}
DEFAULT_ASSERTION = {
    "mode": "snapshot",
    "exclude_fields": ["fetched_at", "collected_at", "request_id", "updated_at"],
    "required_fields": [],
}


@dataclass(frozen=True)
class DebugRun:
    """API 디버깅 한 번의 입력, 요청, 응답, 파싱, 가공 결과 묶음."""

    function: str
    input: dict[str, Any]
    request: dict[str, Any]
    response: dict[str, Any]
    parsed: Any
    processed: Any
    trace: list[str]
    error: dict[str, Any] | None = None
    catalog: dict[str, Any] | None = None


def jsonable(obj: Any) -> Any:
    """Pydantic v2 모델과 날짜/Path 값을 JSON으로 저장 가능한 값으로 변환합니다."""

    if isinstance(obj, BaseModel):
        return obj.model_dump(mode="json")
    if is_dataclass(obj) and not isinstance(obj, type):
        return jsonable(asdict(obj))
    if isinstance(obj, Mapping):
        return {str(key): jsonable(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple, set, frozenset)):
        return [jsonable(item) for item in obj]
    if isinstance(obj, datetime | date):
        return obj.isoformat()
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, bytes):
        return f"<{len(obj)} bytes>"
    return obj


def redact_sensitive(obj: Any) -> Any:
    """dict/list 구조와 문자열 값에서 API key/token 성격의 값을 마스킹합니다."""

    if isinstance(obj, Mapping):
        redacted: dict[str, Any] = {}
        for key, value in obj.items():
            text_key = str(key)
            if text_key.replace("-", "_").lower() in SENSITIVE_KEYS:
                redacted[text_key] = "<REDACTED>"
            else:
                redacted[text_key] = redact_sensitive(value)
        return redacted
    if isinstance(obj, list | tuple):
        return [redact_sensitive(item) for item in obj]
    if isinstance(obj, str):
        return redact_credentials_in_text(obj)
    return obj


def debug_error(exc: Exception) -> dict[str, Any]:
    """예외를 디버그 UI/fixture에 넣기 쉬운 dict로 변환합니다.

    `{type, message, traceback}`은 항상 채워지고, `kma` 자체 예외
    (`KmaError` 서브클래스)이면 `provider`/`endpoint`/`status_code`/
    `result_code`/`failure_kind`/`retryable` 필드도 추가됩니다. 반환값은
    `redact_sensitive()`를 거쳐 인증값이 남지 않습니다.
    """

    payload: dict[str, Any] = {
        "type": exc.__class__.__name__,
        "message": str(exc),
        "traceback": "".join(_traceback.format_exception(type(exc), exc, exc.__traceback__)),
    }
    if isinstance(exc, KmaError):
        payload.update(exc.metadata)
    return cast(dict[str, Any], redact_sensitive(payload))


def save_fixture(
    *,
    base_dir: str | PathLike[str],
    function_name: str,
    case_name: str,
    description: str,
    input_data: Any,
    request_data: Any,
    response_data: Any,
    parsed_result: Any,
    processed_result: Any,
    assertion: Mapping[str, Any] | None = None,
    library_version: str | None = None,
    overwrite: bool = False,
) -> Path:
    """디버그 실행 결과를 pytest replay용 fixture JSON 파일로 저장합니다."""

    safe_case_name = slugify_case_name(case_name)
    fixture_dir = Path(base_dir) / function_name
    fixture_dir.mkdir(parents=True, exist_ok=True)
    fixture_path = fixture_dir / f"{safe_case_name}.json"
    if fixture_path.exists() and not overwrite:
        raise FileExistsError(f"Fixture already exists: {fixture_path}")

    fixture = {
        "name": safe_case_name,
        "function": function_name,
        "description": description,
        "input": redact_sensitive(jsonable(input_data)),
        "request": redact_sensitive(jsonable(request_data)),
        "response": redact_sensitive(jsonable(response_data)),
        "parsed": jsonable(parsed_result),
        "processed": jsonable(processed_result),
        "assertion": dict(assertion or DEFAULT_ASSERTION),
        "meta": {
            "created_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
            "library_version": library_version,
            "source": "debug_ui",
        },
    }
    with fixture_path.open("w", encoding="utf-8") as handle:
        json.dump(fixture, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return fixture_path


def slugify_case_name(value: str) -> str:
    """fixture 파일명에 쓸 수 있도록 case 이름을 느슨하게 정규화합니다."""

    cleaned = value.strip().lower()
    slug = re.sub(r"[^\w.-]+", "-", cleaned, flags=re.UNICODE)
    slug = re.sub(r"-{2,}", "-", slug).strip("-._")
    return slug or "case"
