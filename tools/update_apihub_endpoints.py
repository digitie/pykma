"""APIHub endpoint wrapper generator.

This script reads the public APIHub list pages and writes
`pykma/apihub_endpoints.py`. It intentionally does not call individual data
endpoints and does not require a real `authKey`.
"""

# ruff: noqa: E501

from __future__ import annotations

import html
import json
import keyword
import re
import textwrap
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import unquote, unquote_plus, urlsplit

import requests


BASE_URL = "https://apihub.kma.go.kr"
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "pykma" / "apihub_endpoints.py"
DOC_OUTPUT = ROOT / "docs" / "apihub-endpoints.md"
CATEGORY_IDS = (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15)
CATEGORY_NAMES = {
    2: "지상관측",
    3: "해양관측",
    4: "고층관측",
    5: "레이더",
    6: "위성",
    7: "지진/화산",
    8: "태풍",
    9: "수치모델",
    10: "예특보",
    11: "응용기상",
    12: "세계기상",
    14: "항공기상",
    15: "기후변화",
}


@dataclass
class Endpoint:
    title: str
    category_id: int
    category_name: str
    service_id: int
    service_name: str
    path: str
    parameters: tuple[str, ...]
    sample_params: dict[str, str]
    query_parts: tuple[tuple[str, str], ...]
    response_kind: str
    source: str
    examples: list[dict[str, str]] = field(default_factory=list)
    name: str = ""


@dataclass
class Attachment:
    title: str
    url: str
    filename: str
    category_id: int
    category_name: str
    service_id: int
    service_name: str
    kind: str


def main() -> None:
    session = requests.Session()
    endpoints = scrape_endpoints(session)
    attachments = scrape_attachments(session)
    assign_names(endpoints)
    OUTPUT.write_text(render_module(endpoints, attachments), encoding="utf-8")
    DOC_OUTPUT.write_text(render_docs(endpoints, attachments), encoding="utf-8")
    print(f"wrote {len(endpoints)} endpoint wrappers to {OUTPUT}")
    print(f"captured {len(attachments)} attachment metadata rows")
    print(f"wrote endpoint catalog to {DOC_OUTPUT}")


def scrape_endpoints(session: requests.Session) -> list[Endpoint]:
    merged: OrderedDict[tuple[str, tuple[tuple[str, str], ...]], Endpoint] = OrderedDict()
    services: list[tuple[int, int, str]] = []

    for category_id in CATEGORY_IDS:
        page = get_text(session, "/apiList.do", {"seqApi": category_id})
        for service in parse_const_array(page, "apiList"):
            service_id = int(service["seqApi"])
            service_name = str(service["nmApi"])
            services.append((category_id, service_id, service_name))
            service_page = get_text(
                session,
                "/apiList.do",
                {"seqApi": category_id, "seqApiSub": service_id},
            )
            for endpoint in parse_service_page(category_id, service_id, service_name, service_page):
                merge_endpoint(merged, endpoint)

            generator_page = get_text(
                session,
                "/generateAPIUrl.do",
                {"seqApi": category_id, "seqApiSub": service_id},
            )
            for endpoint in parse_generator_page(
                category_id,
                service_id,
                service_name,
                generator_page,
            ):
                merge_endpoint(merged, endpoint)

            for endpoint in parse_text_attachment_examples(
                session,
                category_id,
                service_id,
                service_name,
                service_page,
            ):
                merge_endpoint(merged, endpoint)

    return list(merged.values())


def scrape_attachments(session: requests.Session) -> list[Attachment]:
    attachments: list[Attachment] = []
    seen: set[tuple[int, int, str, str]] = set()
    for category_id in CATEGORY_IDS:
        page = get_text(session, "/apiList.do", {"seqApi": category_id})
        for service in parse_const_array(page, "apiList"):
            service_id = int(service["seqApi"])
            service_name = str(service["nmApi"])
            service_page = get_text(
                session,
                "/apiList.do",
                {"seqApi": category_id, "seqApiSub": service_id},
            )
            for attachment in parse_attachments(
                category_id,
                service_id,
                service_name,
                service_page,
            ):
                key = (category_id, service_id, attachment.filename, attachment.title)
                if key in seen:
                    continue
                seen.add(key)
                attachments.append(attachment)
    return attachments


def get_text(session: requests.Session, path: str, params: dict[str, Any]) -> str:
    response = session.get(f"{BASE_URL}{path}", params=params, timeout=30)
    response.raise_for_status()
    return response.text


def parse_const_array(text: str, name: str) -> list[dict[str, Any]]:
    match = re.search(rf"const\s+{re.escape(name)}\s*=\s*(\[.*?\]);", text, re.S)
    if not match:
        return []
    return json.loads(match.group(1))


def parse_service_page(
    category_id: int,
    service_id: int,
    service_name: str,
    text: str,
) -> list[Endpoint]:
    endpoints: list[Endpoint] = []
    visible_text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    markers = [
        (match.start(), match.group(1), clean_text(match.group(2)))
        for match in re.finditer(r"<(h3|h4)[^>]*>(.*?)</h[34]>", visible_text, re.S)
    ]
    h4_positions = [marker for marker in markers if marker[1] == "h4"]
    for index, (start, _tag, h4_title) in enumerate(h4_positions):
        h4_title = h4_title.replace("API 활용신청", "").strip()
        end = h4_positions[index + 1][0] if index + 1 < len(h4_positions) else len(visible_text)
        chunk = visible_text[start:end]
        h3_title = ""
        for marker_start, tag, marker_title in markers:
            if marker_start >= start:
                break
            if tag == "h3":
                h3_title = marker_title
        title = " / ".join(part for part in (h3_title, h4_title) if part)
        for raw_url in extract_api_urls(chunk):
            endpoints.append(
                endpoint_from_url(
                    raw_url,
                    category_id,
                    service_id,
                    service_name,
                    title=title,
                    source="apiList.do",
                )
            )
    return endpoints


def parse_generator_page(
    category_id: int,
    service_id: int,
    service_name: str,
    text: str,
) -> list[Endpoint]:
    endpoints: list[Endpoint] = []
    for item in parse_const_array(text, "urlList"):
        route = item.get("seqRoute") or ""
        sample = item.get("sample") or ""
        if not route or not sample:
            continue
        title_parts = [item.get("lv2Nm"), item.get("lv3Nm"), item.get("lv4Nm")]
        title = " / ".join(str(part) for part in title_parts if part)
        endpoints.append(
            endpoint_from_url(
                f"{route}{sample}",
                category_id,
                service_id,
                service_name,
                title=title,
                source="generateAPIUrl.do",
            )
        )
    return endpoints


def parse_text_attachment_examples(
    session: requests.Session,
    category_id: int,
    service_id: int,
    service_name: str,
    text: str,
) -> list[Endpoint]:
    endpoints: list[Endpoint] = []
    for block in re.findall(r'<p class="mt10">(.*?)</p>', text, re.S):
        if "getAttachFile.do" not in block:
            continue
        label = clean_text(block).replace(" 참고자료", "")
        for href in re.findall(r'href="([^"]+)"', block):
            href = html.unescape(href)
            filename = unquote(href.split("fileName=", 1)[-1])
            if not filename.lower().endswith((".txt", ".csv")):
                continue
            if "예제" not in label and filename.lower() != "main.txt":
                continue
            try:
                response = session.get(f"{BASE_URL}{href}", timeout=30)
                response.raise_for_status()
            except requests.RequestException:
                continue
            for raw_url in extract_api_urls(response.text):
                endpoints.append(
                    endpoint_from_url(
                        raw_url,
                        category_id,
                        service_id,
                        service_name,
                        title=f"{label} 예제",
                        source=f"attachment:{filename}",
                    )
                )
    return endpoints


def parse_attachments(
    category_id: int,
    service_id: int,
    service_name: str,
    text: str,
) -> list[Attachment]:
    attachments: list[Attachment] = []
    for block in re.findall(r'<p class="mt10">(.*?)</p>', text, re.S):
        if "getAttachFile.do" not in block:
            continue
        label = clean_text(block).replace(" 참고자료", "")
        for href in re.findall(r'href="([^"]+)"', block):
            href = html.unescape(href)
            filename = unquote(href.split("fileName=", 1)[-1])
            attachments.append(
                Attachment(
                    title=label,
                    url=href,
                    filename=filename,
                    category_id=category_id,
                    category_name=CATEGORY_NAMES[category_id],
                    service_id=service_id,
                    service_name=service_name,
                    kind=classify_attachment(label, filename),
                )
            )
    return attachments


def endpoint_from_url(
    raw_url: str,
    category_id: int,
    service_id: int,
    service_name: str,
    *,
    title: str,
    source: str,
) -> Endpoint:
    cleaned = html.unescape(raw_url).replace("&amp;", "&")
    parts = urlsplit(cleaned if cleaned.startswith("http") else f"{BASE_URL}{cleaned}")
    sample_params, query_parts = parse_query(parts.query)
    return Endpoint(
        title=title or parts.path,
        category_id=category_id,
        category_name=CATEGORY_NAMES[category_id],
        service_id=service_id,
        service_name=service_name,
        path=parts.path,
        parameters=tuple(sample_params.keys()),
        sample_params=sample_params,
        query_parts=query_parts,
        response_kind=classify_response(parts.path),
        source=source,
        examples=[sample_params],
    )


def parse_query(query: str) -> tuple[dict[str, str], tuple[tuple[str, str], ...]]:
    sample_params: OrderedDict[str, str] = OrderedDict()
    query_parts: list[tuple[str, str]] = []
    bare_index = 1
    for raw_part in query.split("&"):
        if raw_part == "":
            continue
        if "=" in raw_part:
            key, value = raw_part.split("=", 1)
            key = unquote_plus(key)
            if key == "authKey":
                continue
            query_parts.append(("named", key))
            sample_params.setdefault(key, unquote_plus(value))
        else:
            name = f"arg{bare_index}"
            bare_index += 1
            query_parts.append(("bare", name))
            sample_params.setdefault(name, unquote_plus(raw_part))
    return dict(sample_params), tuple(query_parts)


def merge_endpoint(
    merged: OrderedDict[tuple[str, tuple[tuple[str, str], ...]], Endpoint],
    endpoint: Endpoint,
) -> None:
    key = (endpoint.path, endpoint.query_parts)
    existing = merged.get(key)
    if existing is None:
        merged[key] = endpoint
        return
    if endpoint.sample_params and endpoint.sample_params not in existing.examples:
        existing.examples.append(endpoint.sample_params)
    if existing.source != endpoint.source and endpoint.source not in existing.source.split(", "):
        existing.source = f"{existing.source}, {endpoint.source}"
    if existing.title == existing.path and endpoint.title:
        existing.title = endpoint.title


def extract_api_urls(text: str) -> list[str]:
    return re.findall(r"https://apihub\.kma\.go\.kr/api/[^\s\"'<>]+", text)


def classify_response(path: str) -> str:
    lower = path.lower()
    if "/typ03/" in lower:
        return "image"
    if "/typ07/" in lower and ("img" in lower or "image" in lower):
        return "image"
    if "/typ04/" in lower or "down" in lower or "file" in lower or lower.endswith("/data"):
        return "file"
    if "/typ02/" in lower or lower.endswith("datalist") or lower.endswith("imagelist"):
        return "structured"
    return "text"


def classify_attachment(label: str, filename: str) -> str:
    target = f"{label} {filename}".lower()
    if "포맷" in label or "format" in target:
        return "format"
    if "예제" in label or "sample" in target or filename.lower() == "main.txt":
        return "sample"
    if filename.lower().endswith((".xlsx", ".xls", ".csv", ".txt")):
        return "data"
    return "reference"


def assign_names(endpoints: list[Endpoint]) -> None:
    seen: dict[str, int] = {}
    reserved = {
        "call_endpoint",
        "endpoint",
        "endpoints",
        "image_endpoint",
        "sample_params",
        "text_endpoint",
    }
    for endpoint in endpoints:
        base = name_from_path(endpoint.path)
        if base in reserved:
            base = f"{base}_api"
        count = seen.get(base, 0) + 1
        seen[base] = count
        endpoint.name = base if count == 1 else f"{base}_{count}"


def name_from_path(path: str) -> str:
    parts = [part for part in path.split("/") if part]
    if "openApi" in parts:
        index = parts.index("openApi")
        parts = parts[index + 1 :]
    else:
        parts = [part for part in parts[2:] if part not in {"url", "cgi", "cgi-bin", "php"}]
    normalized = "_".join(strip_extension(part) for part in parts[-3:])
    normalized = camel_to_snake(normalized)
    normalized = re.sub(r"[^0-9A-Za-z_]+", "_", normalized).strip("_").lower()
    normalized = re.sub(r"_+", "_", normalized)
    if normalized.startswith("nph_"):
        normalized = normalized[4:]
    if not normalized:
        normalized = "endpoint"
    if normalized[0].isdigit() or keyword.iskeyword(normalized):
        normalized = f"api_{normalized}"
    return normalized


def strip_extension(value: str) -> str:
    return re.sub(r"\.(php|do|kfrm|cgi|txt|json|xml)$", "", value, flags=re.I)


def camel_to_snake(value: str) -> str:
    value = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", value)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)


def clean_text(value: str) -> str:
    value = re.sub(r"<script.*?</script>", " ", value, flags=re.S)
    value = re.sub(r"<style.*?</style>", " ", value, flags=re.S)
    value = re.sub(r"<.*?>", " ", value, flags=re.S)
    return " ".join(html.unescape(value).split())


def render_module(endpoints: list[Endpoint], attachments: list[Attachment]) -> str:
    lines = [
        '"""Generated function wrappers for KMA APIHub endpoints.',
        "",
        "This file is generated by `tools/update_apihub_endpoints.py` from",
        "`https://apihub.kma.go.kr/apiList.do` and `generateAPIUrl.do`.",
        f"Generated on {date.today().isoformat()} with {len(endpoints)} endpoint wrappers.",
        '"""',
        "# ruff: noqa: E501",
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any, Mapping",
        "",
        "from .apihub import (",
        "    ApiHubAttachment,",
        "    ApiHubClient,",
        "    ApiHubEndpointSpec,",
        "    ApiHubImage,",
        "    ApiHubResponse,",
        "    ApiHubTextTable,",
        ")",
        "",
        "",
        f"APIHUB_ENDPOINTS: tuple[ApiHubEndpointSpec, ...] = (",
    ]
    for endpoint in endpoints:
        lines.extend(render_spec(endpoint))
    lines.extend(
        [
            ")",
            "",
            "",
            "APIHUB_ATTACHMENTS: tuple[ApiHubAttachment, ...] = (",
        ]
    )
    for attachment in attachments:
        lines.extend(render_attachment(attachment))
    lines.extend(
        [
            ")",
            "",
            "APIHUB_ENDPOINTS_BY_NAME: dict[str, ApiHubEndpointSpec] = {",
            "    endpoint.name: endpoint for endpoint in APIHUB_ENDPOINTS",
            "}",
            "",
            "",
            "class ApiHubGeneratedClient(ApiHubClient):",
            '    """APIHub client with one convenience method per scraped endpoint."""',
            "",
            "    def endpoints(self) -> tuple[ApiHubEndpointSpec, ...]:",
            "        return APIHUB_ENDPOINTS",
            "",
            "    def endpoint(self, name: str) -> ApiHubEndpointSpec:",
            "        return APIHUB_ENDPOINTS_BY_NAME[name]",
            "",
            "    def sample_params(self, name: str) -> Mapping[str, str]:",
            "        return self.endpoint(name).sample_params",
            "",
            "    def call_endpoint(",
            "        self,",
            "        name: str,",
            "        params: Mapping[str, Any] | None = None,",
            "        *,",
            "        use_sample: bool = False,",
            "    ) -> ApiHubResponse:",
            "        spec = self.endpoint(name)",
            "        request_params: dict[str, Any] = {}",
            "        if use_sample:",
            "            request_params.update(spec.sample_params)",
            "        if params:",
            "            request_params.update(params)",
            "        if any(kind == \"bare\" for kind, _name in spec.query_parts):",
            "            return self.request_query_parts(spec.path, spec.query_parts, request_params)",
            "        return self.request_path(spec.path, request_params)",
            "",
            "    def text_endpoint(",
            "        self,",
            "        name: str,",
            "        params: Mapping[str, Any] | None = None,",
            "        *,",
            "        use_sample: bool = False,",
            "        delimiter: str | None = None,",
            "    ) -> ApiHubTextTable:",
            "        return self.call_endpoint(name, params, use_sample=use_sample).text_table(",
            "            delimiter=delimiter",
            "        )",
            "",
            "    def image_endpoint(",
            "        self,",
            "        name: str,",
            "        params: Mapping[str, Any] | None = None,",
            "        *,",
            "        use_sample: bool = False,",
            "    ) -> ApiHubImage:",
            "        return self.call_endpoint(name, params, use_sample=use_sample).image()",
            "",
        ]
    )
    for endpoint in endpoints:
        lines.extend(render_method(endpoint))
    lines.extend(
        [
            "",
            "__all__ = [",
            '    "APIHUB_ATTACHMENTS",',
            '    "APIHUB_ENDPOINTS",',
            '    "APIHUB_ENDPOINTS_BY_NAME",',
            '    "ApiHubGeneratedClient",',
            "]",
            "",
        ]
    )
    return "\n".join(lines)


def render_docs(endpoints: list[Endpoint], attachments: list[Attachment]) -> str:
    counts: dict[str, int] = {}
    for endpoint in endpoints:
        counts[endpoint.response_kind] = counts.get(endpoint.response_kind, 0) + 1

    lines = [
        "# APIHub 함수형 endpoint 목록",
        "",
        f"이 문서는 `{OUTPUT.relative_to(ROOT).as_posix()}`와 같은 원천에서 생성한 함수 목록입니다.",
        "",
        f"- 생성일: {date.today().isoformat()}",
        "- 원천: https://apihub.kma.go.kr/apiList.do",
        "- 보조 원천: https://apihub.kma.go.kr/generateAPIUrl.do",
        "- 텍스트 예제 첨부: `main.txt`처럼 API URL을 포함한 예제 파일",
        f"- 전체 함수형 래퍼: **{len(endpoints)}개**",
        f"- 첨부 자료 metadata: **{len(attachments)}개**",
        "",
        "응답 종류별 개수:",
        "",
        "| 응답 종류 | 개수 | 의미 |",
        "|---|---:|---|",
        f"| `text` | {counts.get('text', 0)} | TXT, CSV식 텍스트, 고정폭 텍스트 |",
        f"| `structured` | {counts.get('structured', 0)} | JSON/XML REST envelope 또는 목록형 응답 |",
        f"| `image` | {counts.get('image', 0)} | 이미지 bytes 또는 그래픽 endpoint |",
        f"| `file` | {counts.get('file', 0)} | GRIB, NetCDF, 원시자료, 다운로드 계열 |",
        "",
        "## 사용법",
        "",
        "```python",
        "from pykma import ApiHubGeneratedClient",
        "",
        "hub = ApiHubGeneratedClient.from_env()",
        "response = hub.kma_sfctm2(tm=\"202605010900\", stn=\"108\", help=\"1\")",
        "rows = response.text_table().rows",
        "```",
        "",
        "홈페이지 예제 값을 그대로 써서 호출하려면 `use_sample=True`를 넘깁니다. 실제 운영 코드에서는 예제 날짜가 오래되었을 수 있으므로 필요한 인자를 명시하는 것을 권장합니다.",
        "",
        "```python",
        "response = hub.kma_sfctm2(use_sample=True, stn=\"108\")",
        "```",
        "",
        "이미지 endpoint는 bytes와 포맷/크기 정보를 함께 얻을 수 있습니다.",
        "",
        "```python",
        "image = hub.image_endpoint(\"api_iwa_img_url_api_ret_grid_img\", use_sample=True)",
        "print(image.format, image.width, image.height)",
        "```",
        "",
        "이름 없는 query string을 쓰는 legacy 그래픽 URL은 `arg1`, `arg2`처럼 순서형 인자로 노출합니다. 예를 들어 `?202305031000&0&...` 형태는 `arg1=\"202305031000\"`, `arg2=\"0\"`로 넘깁니다.",
        "",
        "## 첨부 자료 metadata",
        "",
        "`APIHUB_ATTACHMENTS`에는 포맷정보, 예제, 코드표 같은 첨부 링크를 Python 데이터로 보관합니다. PDF 본문 전체를 패키지에 넣지는 않고, 제목, 파일명, 서비스, 종류, 다운로드 URL을 metadata로 둡니다.",
        "",
        "| 종류 | 개수 |",
        "|---|---:|",
    ]
    attachment_counts: dict[str, int] = {}
    for attachment in attachments:
        attachment_counts[attachment.kind] = attachment_counts.get(attachment.kind, 0) + 1
    for kind in sorted(attachment_counts):
        lines.append(f"| `{kind}` | {attachment_counts[kind]} |")
    lines.extend(
        [
            "",
            "포맷정보와 예제 첨부:",
            "",
            "| 제목 | 서비스 | 종류 | 파일명 |",
            "|---|---|---|---|",
        ]
    )
    for attachment in attachments:
        if attachment.kind not in {"format", "sample"}:
            continue
        lines.append(
            "| "
            f"{attachment.title} | "
            f"{attachment.service_name} | "
            f"`{attachment.kind}` | "
            f"`{attachment.filename}` |"
        )
    lines.append("")

    for category_id in CATEGORY_IDS:
        category_endpoints = [endpoint for endpoint in endpoints if endpoint.category_id == category_id]
        if not category_endpoints:
            continue
        lines.extend(
            [
                f"## {CATEGORY_NAMES[category_id]}",
                "",
                "| 함수 | 서비스 | 응답 | path | 파라미터 |",
                "|---|---|---|---|---|",
            ]
        )
        for endpoint in category_endpoints:
            params = ", ".join(f"`{param}`" for param in endpoint.parameters) or "-"
            lines.append(
                "| "
                f"`{endpoint.name}` | "
                f"{endpoint.service_name} | "
                f"`{endpoint.response_kind}` | "
                f"`{endpoint.path}` | "
                f"{params} |"
            )
        lines.append("")
    return "\n".join(lines)


def render_spec(endpoint: Endpoint) -> list[str]:
    return [
        "    ApiHubEndpointSpec(",
        f"        name={endpoint.name!r},",
        f"        title={endpoint.title!r},",
        f"        category_id={endpoint.category_id!r},",
        f"        category_name={endpoint.category_name!r},",
        f"        service_id={endpoint.service_id!r},",
        f"        service_name={endpoint.service_name!r},",
        f"        path={endpoint.path!r},",
        f"        parameters={endpoint.parameters!r},",
        f"        sample_params={endpoint.sample_params!r},",
        f"        query_parts={endpoint.query_parts!r},",
        f"        response_kind={endpoint.response_kind!r},",
        f"        source={endpoint.source!r},",
        "    ),",
    ]


def render_attachment(attachment: Attachment) -> list[str]:
    return [
        "    ApiHubAttachment(",
        f"        title={attachment.title!r},",
        f"        url={attachment.url!r},",
        f"        filename={attachment.filename!r},",
        f"        category_id={attachment.category_id!r},",
        f"        category_name={attachment.category_name!r},",
        f"        service_id={attachment.service_id!r},",
        f"        service_name={attachment.service_name!r},",
        f"        kind={attachment.kind!r},",
        "    ),",
    ]


def render_method(endpoint: Endpoint) -> list[str]:
    params = ", ".join(endpoint.parameters) if endpoint.parameters else "없음"
    doc = f"{endpoint.title}\n\nPath: {endpoint.path}\n파라미터: {params}"
    doc = "\n".join(textwrap.wrap(doc, width=88, replace_whitespace=False))
    lines = [
        f"    def {endpoint.name}(",
        "        self,",
        "        *,",
        "        use_sample: bool = False,",
        "        **params: Any,",
        "    ) -> ApiHubResponse:",
        f'        """{doc}"""',
        f"        return self.call_endpoint({endpoint.name!r}, params, use_sample=use_sample)",
        "",
    ]
    return lines


if __name__ == "__main__":
    main()
