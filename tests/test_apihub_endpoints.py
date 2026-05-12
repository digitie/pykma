from __future__ import annotations

from typing import Any

from kma.apihub_endpoints import (
    APIHUB_ATTACHMENTS,
    APIHUB_ENDPOINTS,
    APIHUB_ENDPOINTS_BY_NAME,
    ApiHubGeneratedClient,
)


class FakeResponse:
    def __init__(
        self,
        content: bytes,
        *,
        url: str = "https://apihub.kma.go.kr/api/test",
        content_type: str = "application/octet-stream",
    ) -> None:
        self.content = content
        self.text = content.decode("utf-8", errors="replace")
        self.url = url
        self.status_code = 200
        self.headers = {"Content-Type": content_type}

    def raise_for_status(self) -> None:
        return None


class FakeSession:
    def __init__(self, content: bytes = b"ok") -> None:
        self.content = content
        self.calls: list[dict[str, Any]] = []

    def get(self, url: str, *, params: dict[str, Any] | None, timeout: float) -> FakeResponse:
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        return FakeResponse(self.content, url=url)


def test_generated_endpoint_catalog_has_stable_count_and_unique_names() -> None:
    assert len(APIHUB_ENDPOINTS) == 470
    assert len(APIHUB_ENDPOINTS_BY_NAME) == len(APIHUB_ENDPOINTS)
    assert len({(endpoint.path, endpoint.parameters) for endpoint in APIHUB_ENDPOINTS}) == 470


def test_generated_attachment_metadata_includes_format_and_sample_links() -> None:
    assert len(APIHUB_ATTACHMENTS) == 77
    assert any(
        attachment.kind == "format" and "레이더 합성자료" in attachment.title
        for attachment in APIHUB_ATTACHMENTS
    )
    assert any(
        attachment.kind == "sample" and attachment.filename == "main.txt"
        for attachment in APIHUB_ATTACHMENTS
    )


def test_generated_named_wrapper_calls_standard_endpoint() -> None:
    session = FakeSession()
    client = ApiHubGeneratedClient("hub-key", session=session)

    response = client.kma_sfctm2(tm="202605010900", stn="108", help="1")

    assert response.text == "ok"
    assert session.calls[0]["url"] == "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm2.php"
    assert session.calls[0]["params"] == {
        "authKey": "hub-key",
        "tm": "202605010900",
        "stn": "108",
        "help": "1",
    }


def test_generated_named_wrapper_can_use_sample_params() -> None:
    session = FakeSession()
    client = ApiHubGeneratedClient("hub-key", session=session)

    client.kma_sfctm2(use_sample=True, stn="108")

    assert session.calls[0]["params"] == {
        "authKey": "hub-key",
        "tm": "202211300900",
        "stn": "108",
        "help": "1",
    }


def test_generated_wrapper_preserves_bare_query_order() -> None:
    session = FakeSession()
    client = ApiHubGeneratedClient("hub-key", session=session)

    client.aws3_nph_awsm_tms_h06(use_sample=True, arg2="1")

    call = session.calls[0]
    assert call["params"] is None
    assert call["url"].startswith(
        "https://apihub.kma.go.kr/api/typ03/cgi/aws3/nph-awsm_tms_h06"
        "?202305031000&1&108,419"
    )
    assert call["url"].endswith("&_DT=RSW:AWSCHART&authKey=hub-key")


def test_generated_image_endpoint_returns_python_image_metadata() -> None:
    png = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\r"
        b"IHDR"
        + (32).to_bytes(4, "big")
        + (24).to_bytes(4, "big")
        + b"\x08\x02\x00\x00\x00"
    )
    session = FakeSession(png)
    client = ApiHubGeneratedClient("hub-key", session=session)

    image = client.image_endpoint("api_iwa_img_url_api_ret_grid_img", use_sample=True)

    assert image.format == "png"
    assert image.width == 32
    assert image.height == 24
    assert APIHUB_ENDPOINTS_BY_NAME["api_iwa_img_url_api_ret_grid_img"].response_kind == "image"
