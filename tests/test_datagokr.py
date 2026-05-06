from __future__ import annotations

from typing import Any, Callable

from pykma.datagokr import DataGoKrClient
from pykma.exceptions import KmaAuthError, KmaParseError


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.status_code = 200

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self.payload


class FakeSession:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.calls: list[dict[str, Any]] = []

    def get(self, url: str, *, params: dict[str, Any], timeout: float) -> FakeResponse:
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        return FakeResponse(self.payload)


def assert_raises(exc_type: type[BaseException], func: Callable[[], object]) -> None:
    try:
        func()
    except exc_type:
        return
    raise AssertionError(f"expected {exc_type.__name__}")


def _payload(item: Any) -> dict[str, Any]:
    return {
        "response": {
            "header": {"resultCode": "00", "resultMsg": "NORMAL_SERVICE"},
            "body": {"items": {"item": item}},
        }
    }


def test_datagokr_generic_request_builds_service_operation_url() -> None:
    session = FakeSession(_payload([{"wfSv": "맑음"}]))
    client = DataGoKrClient("decoded-key", session=session)

    body = client.request(
        "MidFcstInfoService",
        "getMidFcst",
        {"stnId": "108", "tmFc": "202605010600"},
    )

    assert body["items"]["item"][0]["wfSv"] == "맑음"
    assert session.calls[0]["url"] == "http://apis.data.go.kr/1360000/MidFcstInfoService/getMidFcst"
    assert session.calls[0]["params"]["serviceKey"] == "decoded-key"
    assert session.calls[0]["params"]["dataType"] == "JSON"
    assert session.calls[0]["params"]["pageNo"] == 1
    assert session.calls[0]["params"]["numOfRows"] == 10


def test_datagokr_service_key_parameter_name_is_configurable() -> None:
    session = FakeSession(_payload([{"wfSv": "맑음"}]))
    client = DataGoKrClient("decoded-key", service_key_param="ServiceKey", session=session)

    client.request("MidFcstInfoService", "getMidFcst")

    assert session.calls[0]["params"]["ServiceKey"] == "decoded-key"
    assert "serviceKey" not in session.calls[0]["params"]


def test_datagokr_items_wraps_single_item_dict() -> None:
    client = DataGoKrClient("decoded-key", session=FakeSession(_payload({"wfSv": "맑음"})))

    assert client.items("MidFcstInfoService", "getMidFcst")[0] == {"wfSv": "맑음"}


def test_datagokr_result_code_mapping_and_shape_errors() -> None:
    auth_client = DataGoKrClient(
        "bad-key",
        session=FakeSession(
            {
                "response": {
                    "header": {"resultCode": "30", "resultMsg": "BAD KEY"},
                    "body": {},
                }
            }
        ),
    )
    parse_client = DataGoKrClient("decoded-key", session=FakeSession({"bad": {}}))

    assert_raises(KmaAuthError, lambda: auth_client.request("S", "O"))
    assert_raises(KmaParseError, lambda: parse_client.request("S", "O"))
