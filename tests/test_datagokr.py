from __future__ import annotations

from typing import Any, Callable

from pykma import has_next_page, make_cache_key, next_page_no, sanitize_request_params
from pykma.datagokr import DataGoKrClient
from pykma.exceptions import KmaAuthError, KmaParseError
from pykma.metadata import redact_credentials_in_text


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


def _paged_payload(item: Any, *, page_no: int, total_count: int) -> dict[str, Any]:
    payload = _payload(item)
    payload["response"]["body"].update(
        {"pageNo": page_no, "numOfRows": 1, "totalCount": total_count}
    )
    return payload


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


def test_datagokr_request_with_metadata_sanitizes_service_key() -> None:
    session = FakeSession(_payload([{"wfSv": "맑음"}]))
    client = DataGoKrClient("decoded-key", session=session)

    body, metadata = client.request_with_metadata(
        "MidFcstInfoService",
        "getMidFcst",
        {"stnId": "108", "tmFc": "202605010600"},
    )

    assert body["items"]["item"][0]["wfSv"] == "맑음"
    assert metadata.provider == "data.go.kr"
    assert metadata.endpoint == "MidFcstInfoService/getMidFcst"
    assert metadata.request_params["stnId"] == "108"
    assert "serviceKey" not in metadata.request_params


def test_datagokr_service_key_parameter_name_is_configurable() -> None:
    session = FakeSession(_payload([{"wfSv": "맑음"}]))
    client = DataGoKrClient("decoded-key", service_key_param="ServiceKey", session=session)

    client.request("MidFcstInfoService", "getMidFcst")

    assert session.calls[0]["params"]["ServiceKey"] == "decoded-key"
    assert "serviceKey" not in session.calls[0]["params"]


def test_datagokr_items_wraps_single_item_dict() -> None:
    client = DataGoKrClient("decoded-key", session=FakeSession(_payload({"wfSv": "맑음"})))

    assert client.items("MidFcstInfoService", "getMidFcst")[0] == {"wfSv": "맑음"}


def test_datagokr_pagination_helpers_and_iter_pages_guard() -> None:
    first = _paged_payload([{"id": 1}], page_no=1, total_count=3)
    second = _paged_payload([{"id": 2}], page_no=2, total_count=3)
    third = _paged_payload([{"id": 3}], page_no=3, total_count=3)
    session = FakeSession(first)
    client = DataGoKrClient("decoded-key", session=session)

    assert has_next_page(first["response"]["body"]) is True
    assert next_page_no(first["response"]["body"]) == 2
    assert has_next_page(third["response"]["body"]) is False

    session.payload = first
    pages = []
    for index, body in enumerate(
        client.iter_pages("S", "O", num_of_rows=1, max_pages=2),
        start=1,
    ):
        pages.append(body)
        session.payload = second if index == 1 else third

    assert [page["pageNo"] for page in pages] == [1, 2]


def test_sanitized_params_and_cache_key_ignore_credentials() -> None:
    assert sanitize_request_params({"serviceKey": "secret", "nx": 60}) == {"nx": 60}
    assert redact_credentials_in_text("authKey=secret&tm=0") == "authKey=***&tm=0"

    left = make_cache_key(
        "getVilageFcst",
        {"serviceKey": "secret-a", "dataType": "JSON"},
        base_date="20260507",
        base_time="0200",
        nx=60,
        ny=127,
    )
    right = make_cache_key(
        "getVilageFcst",
        {"serviceKey": "secret-b", "dataType": "JSON"},
        base_date="20260507",
        base_time="0200",
        nx=60,
        ny=127,
    )
    changed_grid = make_cache_key(
        "getVilageFcst",
        {"dataType": "JSON"},
        base_date="20260507",
        base_time="0200",
        nx=61,
        ny=127,
    )

    assert left == right
    assert left != changed_grid


def test_mid_forecast_helpers_do_not_guess_reg_id_mapping() -> None:
    session = FakeSession(
        _payload(
            {
                "regId": "11B00000",
                "tmFc": "202605010600",
                "wf3Am": "맑음",
            }
        )
    )
    client = DataGoKrClient("decoded-key", session=session)

    rows = client.mid_land_forecast(reg_id="11B00000", tm_fc="202605010600")

    assert rows[0].operation == "getMidLandFcst"
    assert rows[0].reg_id == "11B00000"
    assert rows[0].raw["wf3Am"] == "맑음"
    assert rows[0].metadata is not None
    assert rows[0].metadata.request_params["regId"] == "11B00000"
    assert "nx" not in rows[0].metadata.request_params
    assert "ny" not in rows[0].metadata.request_params


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
