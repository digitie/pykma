"""Exception hierarchy for pykma."""

from __future__ import annotations


class KmaError(Exception):
    """Base class for all pykma errors."""

    def __init__(
        self,
        message: str = "",
        *,
        provider: str | None = None,
        endpoint: str | None = None,
        status_code: int | None = None,
        result_code: str | None = None,
        failure_kind: str | None = None,
        retryable: bool | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.endpoint = endpoint
        self.status_code = status_code
        self.result_code = result_code
        self.failure_kind = failure_kind
        self.retryable = retryable

    @property
    def metadata(self) -> dict[str, object]:
        """Return non-empty structured error metadata."""

        values: dict[str, object | None] = {
            "provider": self.provider,
            "endpoint": self.endpoint,
            "status_code": self.status_code,
            "result_code": self.result_code,
            "failure_kind": self.failure_kind,
            "retryable": self.retryable,
        }
        return {key: value for key, value in values.items() if value is not None}


class KmaAuthError(KmaError):
    """Raised when the service key is invalid, expired, or not authorized."""


class KmaRequestError(KmaError):
    """Raised when the request is malformed or rejected by the API."""


class KmaServerError(KmaError):
    """Raised when the KMA API returns a transient server-side failure."""


class KmaParseError(KmaError):
    """Raised when the API response cannot be parsed as expected."""
