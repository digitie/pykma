from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Callable

from kma import (
    KMA_DATA_GOKR_DATASETS,
    ApiCatalogEntry,
    AsosDailyItem,
    AsosHourlyItem,
    WeatherCategory,
    WeatherWarningItem,
    api_catalog,
    api_key_for_gateway,
    env_names_for_gateway,
    has_next_page,
    load_local_env,
    make_cache_key,
    next_page_no,
    sanitize_request_params,
)
from kma.datagokr import AsyncDataGoKrClient, DataGoKrClient
from kma.exceptions import KmaAuthError, KmaParseError, KmaRequestError, KmaServerError
from kma.metadata import redact_credentials_in_text
from kma.time_utils import KST


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.status_code = 200

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self.payload


class XmlErrorResponse:
    status_code = 200
    text = """\ufeff<ns:OpenAPI_ServiceResponse xmlns:ns="urn:kma-error">
<ns:cmmMsgHeader>
<ns:returnAuthMsg>LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR</ns:returnAuthMsg>
<ns:returnReasonCode>22</ns:returnReasonCode>
</ns:cmmMsgHeader></ns:OpenAPI_ServiceResponse>"""

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        raise ValueError("XML body")


class XmlErrorSession:
    def get(self, url: str, *, params: dict[str, Any], timeout: float) -> XmlErrorResponse:
        del url, params, timeout
        return XmlErrorResponse()


class AsyncXmlErrorSession:
    async def get(
        self, url: str, *, params: dict[str, Any], timeout: float
    ) -> XmlErrorResponse:
        del url, params, timeout
        return XmlErrorResponse()


class FakeSession:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.calls: list[dict[str, Any]] = []

    def get(self, url: str, *, params: dict[str, Any], timeout: float) -> FakeResponse:
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        return FakeResponse(self.payload)


class AsyncFakeSession:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.calls: list[dict[str, Any]] = []

    async def get(self, url: str, *, params: dict[str, Any], timeout: float) -> FakeResponse:
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


def _no_data_payload() -> dict[str, Any]:
    # 실서버 NO_DATA 응답은 items가 빈 문자열이거나 body가 비어 있는 등
    # 정상 응답과 다른 shape로 온다.
    return {
        "response": {
            "header": {"resultCode": "03", "resultMsg": "NO_DATA"},
            "body": {"items": "", "pageNo": 1, "numOfRows": 10, "totalCount": 0},
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
    assert session.calls[0]["url"] == "https://apis.data.go.kr/1360000/MidFcstInfoService/getMidFcst"
    assert session.calls[0]["params"]["serviceKey"] == "decoded-key"
    assert session.calls[0]["params"]["dataType"] == "JSON"
    assert session.calls[0]["params"]["pageNo"] == 1
    assert session.calls[0]["params"]["numOfRows"] == 10


def test_datagokr_http_200_xml_quota_is_nonretryable() -> None:
    client = DataGoKrClient("decoded-key", session=XmlErrorSession())

    try:
        client.request("MidFcstInfoService", "getMidFcst")
    except KmaRequestError as error:
        assert error.result_code == "22"
        assert error.failure_kind == "quota"
        assert error.retryable is False
    else:  # pragma: no cover - 실패 메시지 명확화
        raise AssertionError("expected KmaRequestError")


def test_datagokr_async_request_builds_service_operation_url() -> None:
    async def run() -> None:
        session = AsyncFakeSession(_payload([{"wfSv": "맑음"}]))
        client = DataGoKrClient("decoded-key", async_session=session)

        body = await client.arequest(
            "MidFcstInfoService",
            "getMidFcst",
            {"stnId": "108", "tmFc": "202605010600"},
        )

        assert body["items"]["item"][0]["wfSv"] == "맑음"
        assert session.calls[0]["url"] == (
            "https://apis.data.go.kr/1360000/MidFcstInfoService/getMidFcst"
        )
        assert session.calls[0]["params"]["serviceKey"] == "decoded-key"

    asyncio.run(run())


def test_datagokr_async_http_200_xml_quota_is_nonretryable() -> None:
    async def run() -> None:
        client = DataGoKrClient("decoded-key", async_session=AsyncXmlErrorSession())

        try:
            await client.arequest("MidFcstInfoService", "getMidFcst")
        except KmaRequestError as error:
            assert error.result_code == "22"
            assert error.failure_kind == "quota"
            assert error.retryable is False
        else:  # pragma: no cover - 실패 메시지 명확화
            raise AssertionError("expected KmaRequestError")

    asyncio.run(run())


def test_datagokr_aio_returns_async_facade() -> None:
    async def run() -> None:
        session = AsyncFakeSession(_payload([{"wfSv": "맑음"}]))
        client = DataGoKrClient.aio("decoded-key", async_session=session)

        assert isinstance(client, AsyncDataGoKrClient)
        assert client.service_key == "decoded-key"

        async with client:
            body = await client.request(
                "MidFcstInfoService",
                "getMidFcst",
                {"stnId": "108"},
            )
            items = await client.items("MidFcstInfoService", "getMidFcst")

        assert body["items"]["item"][0]["wfSv"] == "맑음"
        assert items[0]["wfSv"] == "맑음"
        assert session.calls[0]["params"]["serviceKey"] == "decoded-key"
        assert client.closed is True

    asyncio.run(run())


def test_datagokr_service_key_strips_copied_whitespace() -> None:
    session = FakeSession(_payload([{"wfSv": "맑음"}]))
    client = DataGoKrClient(" decoded \n key\t", session=session)

    client.request("MidFcstInfoService", "getMidFcst")

    assert session.calls[0]["params"]["serviceKey"] == "decodedkey"


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


def test_datagokr_dataset_catalog_is_kma_only() -> None:
    client = DataGoKrClient("decoded-key", session=FakeSession(_payload([])))

    datasets = client.datasets()

    assert datasets == KMA_DATA_GOKR_DATASETS
    assert len(datasets) == 86
    assert sum(1 for dataset in datasets if dataset.gateway == "datagokr") == 38
    assert sum(1 for dataset in datasets if dataset.gateway == "apihub") == 48
    assert (
        sum(len(dataset.operations) for dataset in datasets if dataset.gateway == "datagokr")
        == 160
    )
    assert all(dataset.title.startswith("\uae30\uc0c1\uccad") for dataset in datasets)
    assert client.dataset("15084084").operations == (
        "getUltraSrtNcst",
        "getUltraSrtFcst",
        "getVilageFcst",
        "getFcstVersion",
    )
    assert len(client.dataset("15000415").operations) == 10
    non_kma_fragments = (
        "\uacbd\uae30\ub3c4",
        "\ub18d\ucd0c\uc9c4\ud765\uccad",
        "\ud589\uc815\uc548\uc804\ubd80",
        "\ubc95\uc81c\ucc98",
        "\ud55c\uad6d\ub3c4\ub85c\uacf5\uc0ac",
    )
    assert not any(
        fragment in dataset.title for dataset in datasets for fragment in non_kma_fragments
    )


def test_api_catalog_flattens_datasets_with_human_readable_labels() -> None:
    client = DataGoKrClient("decoded-key", session=FakeSession(_payload([])))

    rows = api_catalog()
    first = rows[0]
    apihub_row = api_catalog(gateway="apihub")[0]

    assert len(rows) == 208
    assert isinstance(first, ApiCatalogEntry)
    assert first.dataset_name == "기상청_단기예보 조회서비스"
    assert first.operation == "getUltraSrtNcst"
    assert first.label == "기상청_단기예보 조회서비스 / getUltraSrtNcst"
    assert first.credential_param == "serviceKey"
    assert first.service_key_url == first.portal_url
    assert apihub_row.credential_param == "authKey"
    assert "apihub.kma.go.kr" in apihub_row.service_key_url
    assert client.api_catalog(dataset_id="15084084")[0].dataset_name == first.dataset_name


def test_api_catalog_marks_apihub_equivalents() -> None:
    rows = api_catalog()

    # 단기예보 4개 operation 은 APIHub typ02/openApi 에도 동일 path 가 있다.
    short_fcst = [row for row in rows if row.dataset_id == "15084084"]
    assert short_fcst
    ncst = next(row for row in short_fcst if row.operation == "getUltraSrtNcst")
    assert ncst.has_apihub_equivalent is True
    assert ncst.apihub_equivalent_path == (
        "/api/typ02/openApi/VilageFcstInfoService_2.0/getUltraSrtNcst"
    )

    # asdict 에도 새 필드가 노출된다.
    payload = ncst.asdict()
    assert payload["has_apihub_equivalent"] is True
    assert payload["apihub_equivalent_path"].endswith("getUltraSrtNcst")

    # ASOS 일자료(getWthrDataList)는 typ02/openApi 동일 path 가 없어 대체 경로가 없다.
    asos = next(row for row in rows if row.dataset_id == "15059093")
    assert asos.has_apihub_equivalent is False
    assert asos.apihub_equivalent_path is None

    # APIHub LINK dataset 은 data.go.kr REST operation 이 아니므로 False.
    apihub_row = api_catalog(gateway="apihub")[0]
    assert apihub_row.has_apihub_equivalent is False


def test_env_loader_supports_source_specific_keys_and_local_dotenv(
    tmp_path: Any,
    monkeypatch: Any,
) -> None:
    monkeypatch.chdir(tmp_path)
    env_names = (
        "DATA_GO_KR_SERVICE_KEY",
        "KMA_APIHUB_AUTH_KEY",
        "KMA_APIHUB_KEY",
    )
    for name in env_names:
        monkeypatch.delenv(name, raising=False)
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                'DATA_GO_KR_SERVICE_KEY=" data gokr key "',
                "KMA_APIHUB_AUTH_KEY= api hub key",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / ".env.local").write_text(
        "KMA_APIHUB_AUTH_KEY= local api hub key\n",
        encoding="utf-8",
    )

    assert env_names_for_gateway("datagokr") == ("DATA_GO_KR_SERVICE_KEY",)
    assert "DATA_GO_KR_SERVICE_KEY" in load_local_env()
    assert api_key_for_gateway("datagokr") == "datagokrkey"
    assert api_key_for_gateway("apihub") == "localapihubkey"
    assert DataGoKrClient.from_env(session=FakeSession(_payload([]))).service_key == "datagokrkey"


def test_datagokr_dataset_catalog_request_by_id() -> None:
    session = FakeSession(_payload({"stnId": "108", "tm": "2026-05-01"}))
    client = DataGoKrClient("decoded-key", session=session)

    rows = client.dataset_items(
        "15059093",
        {
            "startDt": "20260501",
            "endDt": "20260502",
            "dataCd": "ASOS",
            "dateCd": "DAY",
        },
    )

    assert client.dataset("15059093").service == "AsosDalyInfoService"
    assert session.calls[0]["url"] == (
        "https://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList"
    )
    assert rows[0].service == "AsosDalyInfoService"
    assert rows[0].operation == "getWthrDataList"
    assert rows[0].raw["stnId"] == "108"


def test_datagokr_dataset_catalog_multi_operation_requires_selection() -> None:
    session = FakeSession(_payload({"beachNum": "1", "tm": "202205011600", "wh": "0.7"}))
    client = DataGoKrClient("decoded-key", session=session)

    assert_raises(ValueError, lambda: client.dataset_items("15102239", {"beach_num": "1"}))

    rows = client.dataset_items(
        "15102239",
        {"beach_num": "1", "searchTime": "202205011600"},
        operation="getWhBuoyBeach",
    )

    assert session.calls[0]["url"] == (
        "https://apis.data.go.kr/1360000/BeachInfoservice/getWhBuoyBeach"
    )
    assert rows[0].service == "BeachInfoservice"
    assert rows[0].operation == "getWhBuoyBeach"


def test_datagokr_dataset_catalog_rejects_api_hub_linked_entries() -> None:
    client = DataGoKrClient("decoded-key", session=FakeSession(_payload([])))

    assert client.dataset("15139470").gateway == "apihub"
    assert_raises(ValueError, lambda: client.dataset_items("15139470"))
    assert_raises(ValueError, lambda: client.dataset("99999999"))


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


def test_mid_forecast_helpers_can_select_latest_tm_fc() -> None:
    session = FakeSession(
        _payload(
            {
                "regId": "11B00000",
                "tmFc": "202604301800",
                "wf3Am": "맑음",
            }
        )
    )
    client = DataGoKrClient("decoded-key", session=session)

    rows = client.mid_land_forecast(
        reg_id="11B00000",
        when=datetime(2026, 5, 1, 6, 5, tzinfo=KST),
    )

    assert session.calls[0]["params"]["tmFc"] == "202604301800"
    assert rows[0].tm_fc == "202604301800"
    assert_raises(
        ValueError,
        lambda: client.mid_forecast(stn_id=108, tm_fc="202605010600", when=datetime.now(KST)),
    )


def test_datagokr_mid_sea_forecast_helper() -> None:
    session = FakeSession(
        _payload(
            {
                "regId": "12A20000",
                "tmFc": "202605010600",
                "wf3Am": "맑음",
            }
        )
    )
    client = DataGoKrClient("decoded-key", session=session)

    rows = client.mid_sea_forecast(reg_id="12A20000", tm_fc="202605010600")

    assert rows[0].operation == "getMidSeaFcst"
    assert rows[0].reg_id == "12A20000"
    assert session.calls[0]["url"] == "https://apis.data.go.kr/1360000/MidFcstInfoService/getMidSeaFcst"


def test_mid_forecast_tm_fc_falls_back_to_request_value_when_row_omits_it() -> None:
    # 실서버 MidFcstInfoService 응답 row는 요청의 tmFc를 에코하지 않는다 (#20).
    # 응답에 tmFc가 없으면 요청에 실제로 사용한 tmFc로 폴백해야 한다.
    calls: list[tuple[Callable[[DataGoKrClient], Any], str, dict[str, Any]]] = [
        (
            lambda c: c.mid_forecast(stn_id=108, tm_fc="202606120600"),
            "getMidFcst",
            {"stnId": "108", "wfSv": "맑음"},
        ),
        (
            lambda c: c.mid_land_forecast(reg_id="11B00000", tm_fc="202606120600"),
            "getMidLandFcst",
            {"regId": "11B00000", "wf3Am": "맑음"},
        ),
        (
            lambda c: c.mid_temperature_forecast(reg_id="11B10101", tm_fc="202606120600"),
            "getMidTa",
            {"regId": "11B10101", "taMin3": "12"},
        ),
        (
            lambda c: c.mid_sea_forecast(reg_id="12A20000", tm_fc="202606120600"),
            "getMidSeaFcst",
            {"regId": "12A20000", "wf3Am": "맑음"},
        ),
    ]
    for call, operation, row in calls:
        session = FakeSession(_payload(dict(row)))
        client = DataGoKrClient("decoded-key", session=session)

        rows = call(client)

        assert session.calls[0]["params"]["tmFc"] == "202606120600", operation
        assert rows[0].operation == operation
        assert rows[0].tm_fc == "202606120600", operation
        # raw는 원본 그대로 보존 — 폴백 값을 주입하지 않는다.
        assert "tmFc" not in rows[0].raw, operation


def test_mid_forecast_tm_fc_prefers_response_row_value_over_request() -> None:
    session = FakeSession(
        _payload(
            {
                "regId": "11B00000",
                "tmFc": "202606111800",
                "wf3Am": "맑음",
            }
        )
    )
    client = DataGoKrClient("decoded-key", session=session)

    rows = client.mid_land_forecast(reg_id="11B00000", tm_fc="202606120600")

    assert session.calls[0]["params"]["tmFc"] == "202606120600"
    assert rows[0].tm_fc == "202606111800"


def test_mid_forecast_tm_fc_fallback_handles_empty_row_value() -> None:
    session = FakeSession(
        _payload(
            {
                "regId": "11B00000",
                "tmFc": "",
                "wf3Am": "맑음",
            }
        )
    )
    client = DataGoKrClient("decoded-key", session=session)

    rows = client.mid_land_forecast(reg_id="11B00000", tm_fc="202606120600")

    assert rows[0].tm_fc == "202606120600"


def test_mid_forecast_tm_fc_fallback_matches_auto_resolved_request_value() -> None:
    # when= 자동 해석(tm_fc 생략) 경로에서도 요청 param과 item 폴백이 같은 값을 본다.
    session = FakeSession(_payload({"regId": "11B00000", "wf3Am": "맑음"}))
    client = DataGoKrClient("decoded-key", session=session)

    rows = client.mid_land_forecast(
        reg_id="11B00000",
        when=datetime(2026, 6, 12, 6, 5, tzinfo=KST),
    )

    assert session.calls[0]["params"]["tmFc"] == "202606111800"
    assert rows[0].tm_fc == "202606111800"


def test_datagokr_asos_helpers_build_requests() -> None:
    daily_session = FakeSession(
        _payload(
            {
                "stnId": "108",
                "stnNm": "서울",
                "tm": "2026-05-01",
                "avgTa": "18.3",
                "minTa": "12.1",
                "maxTa": "24.5",
                "sumRn": "",
                "avgWs": "2.4",
                "avgRhm": "55.0",
            }
        )
    )
    hourly_session = FakeSession(
        _payload(
            {
                "stnId": "108",
                "stnNm": "서울",
                "tm": "2026-05-01 03:00",
                "ta": "14.2",
                "rn": "",
                "ws": "1.8",
                "wd": "270",
                "hm": "62",
                "pa": "1009.3",
                "ps": "1013.1",
            }
        )
    )

    daily = DataGoKrClient("decoded-key", session=daily_session).asos_daily_weather(
        start_dt="20260501",
        end_dt="20260502",
        stn_ids=108,
    )
    hourly = DataGoKrClient("decoded-key", session=hourly_session).asos_hourly_weather(
        start_dt="20260501",
        start_hh=3,
        end_dt="20260501",
        end_hh="05",
        stn_ids="108",
    )

    assert daily_session.calls[0]["url"] == (
        "https://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList"
    )
    assert daily_session.calls[0]["params"]["dataCd"] == "ASOS"
    assert daily_session.calls[0]["params"]["dateCd"] == "DAY"
    assert daily_session.calls[0]["params"]["stnIds"] == "108"
    assert isinstance(daily[0], AsosDailyItem)
    assert daily[0].stn_id == "108"
    assert daily[0].stn_name == "서울"
    assert daily[0].date == "2026-05-01"
    assert daily[0].avg_temperature == 18.3
    assert daily[0].max_temperature == 24.5
    assert daily[0].precipitation is None  # 빈 문자열 -> None
    assert daily[0].avg_humidity == 55.0
    assert daily[0].raw["stnNm"] == "서울"
    assert daily[0].metadata is not None
    assert "serviceKey" not in daily[0].metadata.request_params

    assert hourly_session.calls[0]["params"]["startHh"] == "03"
    assert hourly_session.calls[0]["params"]["endHh"] == "05"
    assert isinstance(hourly[0], AsosHourlyItem)
    assert hourly[0].observed_at == "2026-05-01 03:00"
    assert hourly[0].temperature == 14.2
    assert hourly[0].precipitation is None
    assert hourly[0].wind_direction == 270.0
    assert hourly[0].humidity == 62.0
    assert hourly[0].sea_level_pressure == 1013.1


def test_datagokr_raw_weather_warning_and_message_helpers() -> None:
    warning_session = FakeSession(
        _payload(
            {
                "stnId": "108",
                "tmFc": "202605010600",
                "tmSeq": "1",
                "title": "[기상특보] 서울 강풍주의보",
            }
        )
    )
    message_session = FakeSession(_payload({"wfSv1": "summary"}))

    warning = DataGoKrClient("decoded-key", session=warning_session).weather_warning_list(
        stn_id=108,
        from_tm_fc="20260501",
        to_tm_fc="20260502",
    )
    land = DataGoKrClient("decoded-key", session=message_session).land_forecast_message(
        reg_id="11B10101"
    )

    assert warning_session.calls[0]["url"] == (
        "https://apis.data.go.kr/1360000/WthrWrnInfoService/getWthrWrnList"
    )
    assert warning_session.calls[0]["params"]["fromTmFc"] == "20260501"
    assert isinstance(warning[0], WeatherWarningItem)
    assert warning[0].stn_id == "108"
    assert warning[0].tm_fc == "202605010600"
    assert warning[0].seq == "1"
    assert warning[0].title == "[기상특보] 서울 강풍주의보"
    assert warning[0].metadata is not None
    assert "serviceKey" not in warning[0].metadata.request_params
    assert message_session.calls[0]["url"] == (
        "https://apis.data.go.kr/1360000/VilageFcstMsgService/getLandFcst"
    )
    assert message_session.calls[0]["params"]["regId"] == "11B10101"
    assert land[0].operation == "getLandFcst"


def test_datagokr_beach_forecast_helper_builds_request_and_models_rows() -> None:
    session = FakeSession(
        _payload(
            {
                "beachNum": "1",
                "baseDate": "20220622",
                "baseTime": "1230",
                "category": "TMP",
                "fcstDate": "20220622",
                "fcstTime": "1300",
                "fcstValue": "25.1",
                "nx": "51",
                "ny": "124",
            }
        )
    )
    client = DataGoKrClient("decoded-key", session=session)

    rows = client.beach_ultra_short_forecast(
        beach_num=1,
        base_date="20220622",
        base_time="1230",
    )

    assert session.calls[0]["url"] == (
        "https://apis.data.go.kr/1360000/BeachInfoservice/getUltraSrtFcstBeach"
    )
    assert session.calls[0]["params"]["serviceKey"] == "decoded-key"
    assert session.calls[0]["params"]["dataType"] == "JSON"
    assert session.calls[0]["params"]["numOfRows"] == 1000
    assert session.calls[0]["params"]["beach_num"] == "1"
    assert rows[0].operation == "getUltraSrtFcstBeach"
    assert rows[0].category is WeatherCategory.TEMPERATURE
    assert rows[0].value == 25.1
    assert rows[0].grid is not None
    assert rows[0].grid.nx == 51
    assert rows[0].latlon is not None
    assert rows[0].metadata is not None
    assert rows[0].metadata.endpoint == "BeachInfoservice/getUltraSrtFcstBeach"
    assert rows[0].metadata.base_date == "20220622"
    assert "serviceKey" not in rows[0].metadata.request_params


def test_datagokr_beach_forecast_can_select_latest_base_from_when() -> None:
    session = FakeSession(
        _payload(
            {
                "beachNum": "1",
                "baseDate": "20260506",
                "baseTime": "2300",
                "category": "SKY",
                "fcstDate": "20260507",
                "fcstTime": "0000",
                "fcstValue": "1",
                "nx": "51",
                "ny": "124",
            }
        )
    )
    client = DataGoKrClient("decoded-key", session=session)

    client.beach_forecast(beach_num="1", when=datetime(2026, 5, 7, 2, 5, tzinfo=KST))

    assert session.calls[0]["params"]["base_date"] == "20260506"
    assert session.calls[0]["params"]["base_time"] == "2300"
    assert_raises(
        ValueError,
        lambda: client.beach_forecast(beach_num="1", base_date="20260507"),
    )


def test_datagokr_beach_observation_helpers_parse_rows() -> None:
    wave_client = DataGoKrClient(
        "decoded-key",
        session=FakeSession(_payload({"beachNum": "1", "tm": "202205011600", "wh": "0.7"})),
    )
    water_client = DataGoKrClient(
        "decoded-key",
        session=FakeSession(_payload({"beachNum": "1", "tm": "202205011600", "tw": "18.4"})),
    )

    wave = wave_client.beach_wave_height(beach_num="1", search_time="202205011600")
    water = water_client.beach_water_temperature(
        beach_num=1,
        search_time=datetime(2022, 5, 1, 16, 0, tzinfo=KST),
    )

    assert wave[0].observed_at.isoformat() == "2022-05-01T16:00:00+09:00"
    assert wave[0].wave_height == 0.7
    assert water[0].water_temperature == 18.4


def test_datagokr_beach_tide_and_sun_helpers_preserve_upstream_parameters() -> None:
    tide_client = DataGoKrClient(
        "decoded-key",
        session=FakeSession(
            _payload(
                {
                    "beachNum": "1",
                    "baseDate": "20220620",
                    "tiStnld": "station",
                    "tiTime": "0520",
                    "tiType": "low",
                    "tilevel": "35",
                }
            )
        ),
    )
    sun_session = FakeSession(
        _payload(
            {
                "beachNum": "1",
                "baseDate": "20220501",
                "sunrise": "0535",
                "sunset": "1920",
            }
        )
    )
    sun_client = DataGoKrClient("decoded-key", session=sun_session)

    tide = tide_client.beach_tide_info(beach_num=1, base_date="20220620")
    sun = sun_client.beach_sun_info(beach_num="1", base_date="20220501")

    assert tide[0].station_name == "station"
    assert tide[0].tide_level == 35.0
    assert sun[0].sunrise == "0535"
    assert sun_session.calls[0]["params"]["Base_date"] == "20220501"
    assert sun[0].metadata is not None
    assert sun[0].metadata.base_date == "20220501"


def test_datagokr_tour_living_and_earthquake_helpers() -> None:
    tour_session = FakeSession(_payload({"courseId": "1"}))
    living_session = FakeSession(_payload({"areaNo": "1100000000"}))
    quake_session = FakeSession(_payload({"tmFc": "20260501"}))

    tour = DataGoKrClient("decoded-key", session=tour_session).tour_village_forecast(
        course_id=1,
        current_date="20260501",
        hour=9,
    )
    uv = DataGoKrClient("decoded-key", session=living_session).uv_index(
        area_no="1100000000",
        time="2026050106",
    )
    quake = DataGoKrClient("decoded-key", session=quake_session).earthquake_message_list(
        from_tm_fc="20260501",
        to_tm_fc="20260502",
    )

    assert tour_session.calls[0]["url"] == (
        "https://apis.data.go.kr/1360000/TourStnInfoService1/getTourStnVilageFcst1"
    )
    assert tour_session.calls[0]["params"]["HOUR"] == "09"
    assert tour[0].service == "TourStnInfoService1"
    assert living_session.calls[0]["url"] == (
        "https://apis.data.go.kr/1360000/LivingWthrIdxServiceV4/getUVIdxV4"
    )
    assert living_session.calls[0]["params"]["time"] == "2026050106"
    assert uv[0].operation == "getUVIdxV4"
    assert quake_session.calls[0]["url"] == (
        "https://apis.data.go.kr/1360000/EqkInfoService/getEqkMsgList"
    )
    assert quake_session.calls[0]["params"]["toTmFc"] == "20260502"
    assert quake[0].operation == "getEqkMsgList"


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
    server_client = DataGoKrClient(
        "decoded-key",
        session=FakeSession(
            {
                "response": {
                    "header": {"resultCode": "99", "resultMsg": "UNKNOWN_ERROR"},
                    "body": {},
                }
            }
        ),
    )
    parse_client = DataGoKrClient("decoded-key", session=FakeSession({"bad": {}}))

    assert_raises(KmaAuthError, lambda: auth_client.request("S", "O"))
    assert_raises(KmaServerError, lambda: server_client.request("S", "O"))
    assert_raises(KmaParseError, lambda: parse_client.request("S", "O"))


def test_datagokr_no_data_result_code_normalizes_to_empty_body() -> None:
    client = DataGoKrClient("decoded-key", session=FakeSession(_no_data_payload()))

    body = client.request("MidFcstInfoService", "getMidFcst")

    assert body["items"] == {"item": []}
    assert body["totalCount"] == 0
    assert body["pageNo"] == 1
    assert has_next_page(body) is False


def test_datagokr_no_data_weather_warning_list_returns_empty_list() -> None:
    session = FakeSession(_no_data_payload())
    client = DataGoKrClient("decoded-key", session=session)

    warnings = client.weather_warning_list(
        stn_id=108,
        from_tm_fc="20260501",
        to_tm_fc="20260504",
    )

    assert warnings == []
    assert session.calls[0]["url"] == (
        "https://apis.data.go.kr/1360000/WthrWrnInfoService/getWthrWrnList"
    )


def test_datagokr_no_data_mid_forecast_returns_empty_list() -> None:
    client = DataGoKrClient("decoded-key", session=FakeSession(_no_data_payload()))

    assert client.mid_forecast(stn_id=108, tm_fc="202605010600") == []


def test_datagokr_no_data_iter_pages_stops_after_first_page() -> None:
    session = FakeSession(_no_data_payload())
    client = DataGoKrClient("decoded-key", session=session)

    pages = list(client.iter_pages("WthrWrnInfoService", "getWthrWrnList"))

    assert len(pages) == 1
    assert pages[0]["items"] == {"item": []}
    assert len(session.calls) == 1


def test_datagokr_no_data_without_body_returns_empty_items() -> None:
    payload = {"response": {"header": {"resultCode": "03", "resultMsg": "NO_DATA"}}}
    client = DataGoKrClient("decoded-key", session=FakeSession(payload))

    assert client.items("WthrWrnInfoService", "getWthrWrnList") == []


def test_datagokr_no_data_async_items_returns_empty_list() -> None:
    async def run() -> None:
        session = AsyncFakeSession(_no_data_payload())
        client = DataGoKrClient("decoded-key", async_session=session)

        items = await client.aitems("WthrWrnInfoService", "getWthrWrnList")

        assert items == []

    asyncio.run(run())
