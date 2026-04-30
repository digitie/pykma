from __future__ import annotations

from typing import Any, Callable

from pykma.apihub import (
    ApiHubClient,
    extract_apihub_endpoints,
    parse_apihub_sample_url,
    parse_apihub_services,
)


class FakeResponse:
    def __init__(
        self,
        text: str,
        *,
        url: str = "https://apihub.kma.go.kr/api/test",
        status_code: int = 200,
        content_type: str = "text/plain; charset=UTF-8",
    ) -> None:
        self.text = text
        self.content = text.encode("utf-8")
        self.url = url
        self.status_code = status_code
        self.headers = {"Content-Type": content_type}

    def raise_for_status(self) -> None:
        return None


class FakeSession:
    def __init__(self, text: str) -> None:
        self.text = text
        self.calls: list[dict[str, Any]] = []

    def get(self, url: str, *, params: dict[str, Any], timeout: float) -> FakeResponse:
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        return FakeResponse(self.text, url=url)


def assert_raises(exc_type: type[BaseException], func: Callable[[], object]) -> None:
    try:
        func()
    except exc_type:
        return
    raise AssertionError(f"expected {exc_type.__name__}")


def test_parse_apihub_services_from_portal_script() -> None:
    html = """
    <script>
    const apiList = [{"seqApi":238,"nmApi":"종관기상관측(ASOS)"},{"seqApi":239,"nmApi":"방재기상관측(AWS)"}];
    </script>
    """

    services = parse_apihub_services(html, 2)

    assert [service.service_id for service in services] == [238, 239]
    assert services[0].category_name == "지상관측"
    assert services[0].service_name == "종관기상관측(ASOS)"


def test_parse_apihub_sample_url_removes_auth_key_and_preserves_params() -> None:
    endpoint = parse_apihub_sample_url(
        "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm2.php?"
        "tm=202211300900&amp;stn=0&amp;help=1&amp;authKey=secret"
    )

    assert endpoint.path == "/api/typ01/url/kma_sfctm2.php"
    assert endpoint.parameters == ("tm", "stn", "help")
    assert endpoint.sample_params == {"tm": "202211300900", "stn": "0", "help": "1"}


def test_extract_apihub_endpoints_deduplicates_generated_urls() -> None:
    html = """
    https://apihub.kma.go.kr/api/typ01/url/wrn_reg.php?tmfc=0&amp;authKey=a
    https://apihub.kma.go.kr/api/typ01/url/wrn_reg.php?tmfc=0&authKey=a
    https://apihub.kma.go.kr/api/typ01/url/wrn_met_data.php?reg=0&wrn=A&authKey=a
    """

    endpoints = extract_apihub_endpoints(html)

    assert len(endpoints) == 2
    assert endpoints[0].path == "/api/typ01/url/wrn_reg.php"
    assert endpoints[1].parameters == ("reg", "wrn")


def test_apihub_request_path_appends_auth_key() -> None:
    session = FakeSession("ok")
    client = ApiHubClient("hub-key", session=session)

    response = client.request_path("/api/typ01/url/kma_sfctm2.php", {"tm": "202211300900"})

    assert response.text == "ok"
    assert session.calls[0]["url"] == "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm2.php"
    assert session.calls[0]["params"] == {"authKey": "hub-key", "tm": "202211300900"}


def test_apihub_open_api_builds_typ02_path_and_defaults() -> None:
    session = FakeSession('{"response": "ok"}')
    client = ApiHubClient("hub-key", session=session)

    response = client.open_api(
        "MidFcstInfoService",
        "getMidFcst",
        {"stnId": "108", "tmFc": "202605010600"},
    )

    assert response.json() == {"response": "ok"}
    assert session.calls[0]["url"].endswith("/api/typ02/openApi/MidFcstInfoService/getMidFcst")
    assert session.calls[0]["params"]["authKey"] == "hub-key"
    assert session.calls[0]["params"]["dataType"] == "JSON"
    assert session.calls[0]["params"]["pageNo"] == 1
    assert session.calls[0]["params"]["numOfRows"] == 10


def test_apihub_rejects_non_api_paths() -> None:
    client = ApiHubClient("hub-key", session=FakeSession("ok"))

    assert_raises(ValueError, lambda: client.request_path("/noticeList.do"))


def test_apihub_discover_services_and_endpoints_use_portal_pages() -> None:
    service_html = 'const apiList = [{"seqApi":288,"nmApi":"기상특보"}];'
    endpoint_html = "https://apihub.kma.go.kr/api/typ01/url/wrn_reg.php?tmfc=0&authKey=secret"
    session = FakeSession(service_html)
    client = ApiHubClient("hub-key", session=session)

    services = client.discover_services((10,))
    session.text = endpoint_html
    endpoints = client.discover_endpoints(services[0].category_id, services[0].service_id)

    assert services[0].service_name == "기상특보"
    assert endpoints[0].path == "/api/typ01/url/wrn_reg.php"
    assert session.calls[0]["url"] == "https://apihub.kma.go.kr/apiList.do"
    assert session.calls[0]["params"] == {"seqApi": 10}
    assert session.calls[1]["params"] == {"seqApi": 10, "seqApiSub": 288}

