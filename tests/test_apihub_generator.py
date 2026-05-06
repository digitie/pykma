from __future__ import annotations

from typing import Any

from requests import HTTPError

from tools import update_apihub_endpoints as generator


class FakeResponse:
    def __init__(self, text: str, *, fail: bool = False) -> None:
        self.text = text
        self.fail = fail

    def raise_for_status(self) -> None:
        if self.fail:
            raise HTTPError("500 Server Error")


class FakeSession:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def get(self, url: str, *, params: dict[str, Any], timeout: float) -> FakeResponse:
        self.calls.append((url, params))
        if url.endswith("/apiList.do") and "seqApiSub" not in params:
            return FakeResponse('const apiList = [{"seqApi":238,"nmApi":"테스트서비스"}];')
        if url.endswith("/apiList.do"):
            return FakeResponse(
                "<h3>테스트 묶음</h3>"
                "<h4>1. 테스트 API 활용신청</h4>"
                "https://apihub.kma.go.kr/api/typ01/url/test.php?a=1&authKey={인증키입력}"
            )
        if url.endswith("/generateAPIUrl.do"):
            return FakeResponse("server error", fail=True)
        raise AssertionError(f"unexpected URL: {url}")


def test_scrape_endpoints_keeps_api_list_when_generator_page_fails() -> None:
    original_categories = generator.CATEGORY_IDS
    generator.CATEGORY_IDS = (2,)
    try:
        endpoints = generator.scrape_endpoints(FakeSession())  # type: ignore[arg-type]
    finally:
        generator.CATEGORY_IDS = original_categories

    assert len(endpoints) == 1
    assert endpoints[0].path == "/api/typ01/url/test.php"
    assert endpoints[0].parameters == ("a",)
