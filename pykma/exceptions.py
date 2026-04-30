"""Exception hierarchy for pykma."""


class KmaError(Exception):
    """Base class for all pykma errors."""


class KmaAuthError(KmaError):
    """Raised when the service key is invalid, expired, or not authorized."""


class KmaRequestError(KmaError):
    """Raised when the request is malformed or rejected by the API."""


class KmaServerError(KmaError):
    """Raised when the KMA API returns a transient server-side failure."""


class KmaParseError(KmaError):
    """Raised when the API response cannot be parsed as expected."""

