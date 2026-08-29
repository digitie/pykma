"""`kma` 응답 metadata와 민감정보 제거 도우미."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qsl, urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator

_CREDENTIAL_PARAM_NAMES = {
    "apikey",
    "api_key",
    "authkey",
    "auth_key",
    "key",
    "servicekey",
    "service_key",
}
_CREDENTIAL_TEXT_RE = re.compile(
    r"(?i)\b(api_key|apiKey|auth_key|authKey|key|service_key|serviceKey)=([^&\s]+)"
)


class ResponseMetadata(BaseModel):
    """`kma` 응답 모델의 제공자 출처 정보.

    `request_params`는 입력 시 정리되며 `serviceKey`, `authKey`, `key` 같은
    원본 인증값을 보관하지 않습니다.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: str
    service_name: str
    endpoint: str
    request_params: dict[str, Any] = Field(default_factory=dict)
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    base_date: str | None = None
    base_time: str | None = None
    reference_time: datetime | None = None

    @field_validator("request_params", mode="before")
    @classmethod
    def _sanitize_params(cls, value: object) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, Mapping):
            raise TypeError("request_params must be a mapping")
        return sanitize_request_params(value)


def is_credential_param(name: str) -> bool:
    """파라미터 이름이 API 인증값을 담는 것으로 알려져 있는지 반환합니다."""

    return name.replace("-", "_").lower() in _CREDENTIAL_PARAM_NAMES


def sanitize_request_params(params: Mapping[str, Any]) -> dict[str, Any]:
    """인증값을 담는 key를 제거한 요청 파라미터를 반환합니다.

    이 도우미는 의도적으로 보수적입니다. `serviceKey`, `authKey`, `key`와
    흔한 snake_case 변형은 masking이 아니라 삭제해서 로그, cache key,
    모델 repr에 인증값이 들어가지 않게 합니다.
    """

    sanitized: dict[str, Any] = {}
    for key, value in params.items():
        text_key = str(key)
        if is_credential_param(text_key):
            continue
        sanitized[text_key] = _sanitize_value(value)
    return sanitized


def redact_credentials_in_text(text: str) -> str:
    """자유 형식 제공자 텍스트에서 인증 query 값을 가립니다."""

    return _CREDENTIAL_TEXT_RE.sub(lambda match: f"{match.group(1)}=***", text)


def request_params_from_url(url: str) -> dict[str, Any]:
    """URL에서 민감정보가 제거된 query mapping을 추출합니다.

    일부 APIHub legacy URL의 이름 없는 query 조각은 `arg1`, `arg2`처럼 저장합니다.
    """

    query = urlsplit(url).query
    if not query:
        return {}

    params: dict[str, Any] = {}
    bare_index = 1
    for raw_part in query.split("&"):
        if not raw_part:
            continue
        if "=" in raw_part:
            for key, value in parse_qsl(raw_part, keep_blank_values=True):
                params[key] = value
        else:
            params[f"arg{bare_index}"] = raw_part
            bare_index += 1
    return sanitize_request_params(params)


def make_response_metadata(
    *,
    provider: str,
    service_name: str,
    endpoint: str,
    request_params: Mapping[str, Any] | None = None,
    collected_at: datetime | None = None,
    base_date: str | None = None,
    base_time: str | None = None,
    reference_time: datetime | None = None,
) -> ResponseMetadata:
    """제공자 응답의 민감정보 제거된 출처 metadata를 만듭니다."""

    return ResponseMetadata(
        provider=provider,
        service_name=service_name,
        endpoint=endpoint,
        request_params=sanitize_request_params(request_params or {}),
        collected_at=collected_at or datetime.now(timezone.utc),
        base_date=base_date,
        base_time=base_time,
        reference_time=reference_time,
    )


def make_cache_key(
    endpoint: str,
    params: Mapping[str, Any] | None = None,
    *,
    base_date: str | None = None,
    base_time: str | None = None,
    nx: int | None = None,
    ny: int | None = None,
    namespace: str = "kma:v1",
) -> str:
    """endpoint와 민감정보 제거된 요청 입력으로 안정적인 cache key를 반환합니다."""

    clean_params = sanitize_request_params(params or {})
    if base_date is not None:
        clean_params["base_date"] = base_date
    if base_time is not None:
        clean_params["base_time"] = base_time
    if nx is not None:
        clean_params["nx"] = nx
    if ny is not None:
        clean_params["ny"] = ny

    payload = {
        "endpoint": str(endpoint),
        "params": _canonical_jsonable(clean_params),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return f"{namespace}:{digest}"


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return sanitize_request_params(value)
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_sanitize_value(item) for item in value)
    return value


def _canonical_jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _canonical_jsonable(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [_canonical_jsonable(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    return value
