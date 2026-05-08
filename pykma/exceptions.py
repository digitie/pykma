"""`pykma` 예외 계층."""

from __future__ import annotations


class KmaError(Exception):
    """모든 `pykma` 예외의 기본 클래스."""

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
        """비어 있지 않은 구조화 오류 metadata를 반환합니다."""

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
    """인증키가 잘못되었거나 만료되었거나 권한이 없을 때 발생합니다."""


class KmaRequestError(KmaError):
    """요청이 잘못되었거나 API가 요청을 거부했을 때 발생합니다."""


class KmaServerError(KmaError):
    """API가 일시적인 서버 측 실패를 반환했을 때 발생합니다."""


class KmaParseError(KmaError):
    """API 응답을 기대한 구조로 파싱할 수 없을 때 발생합니다."""
