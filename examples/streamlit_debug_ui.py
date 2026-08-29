"""Streamlit 기반 기상청 API 디버그 카탈로그 뷰어."""
# ruff: noqa: E402,I001

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
for module_name, module in list(sys.modules.items()):
    if module_name != "kma" and not module_name.startswith("kma."):
        continue
    module_file = getattr(module, "__file__", None)
    if module_file is not None and not Path(module_file).resolve().is_relative_to(SRC):
        del sys.modules[module_name]

try:
    import pandas as pd
    import streamlit as st
except ModuleNotFoundError as exc:  # pragma: no cover - 선택 실행 도구
    raise SystemExit('Streamlit UI를 쓰려면 `pip install -e ".[debug-ui]"`를 실행하세요.') from exc

from kma import (
    ApiCatalogEntry,
    ApiHubGeneratedClient,
    DataGoKrClient,
    DebugRun,
    api_catalog,
    api_key_for_gateway,
    apihub_endpoint_catalog,
    debug_error,
    env_names_for_gateway,
    jsonable,
    load_local_env,
    redact_sensitive,
    save_fixture,
)

# 요청 파라미터 중 고정된 선택지가 있는 것으로 알려진 이름 -> selectbox choices.
# `dataType`/`type`은 data.go.kr/APIHub 양쪽에서 흔히 쓰는 응답 형식 파라미터다.
# kma의 `enums.py`(WeatherCategory, SkyCode 등)는 응답 값 분류용이라 요청
# 파라미터로는 재사용하지 않는다 — 실제로 요청 파라미터로 쓰이는 enum이 없다.
_ENUM_CHOICES: dict[str, tuple[str, ...]] = {
    "dataType": ("JSON", "XML"),
    "type": ("json", "xml"),
}

_RESPONSE_KIND_DESCRIPTIONS: dict[str, str] = {
    "structured": "JSON/XML 구조화 응답을 반환합니다.",
    "text": "공백/CSV로 구분된 legacy text 응답을 표 형태로 파싱해 반환합니다.",
    "image": "이미지(binary) 응답입니다 — 크기/포맷 metadata만 표시합니다.",
    "file": "파일(binary) 응답입니다 — 크기/타입 metadata만 표시합니다.",
}


@dataclass(frozen=True)
class ParameterSpec:
    """디버그 UI에서 요청 파라미터 입력 폼을 만들기 위한 최소 명세."""

    name: str
    required: bool
    label: str
    help: str = ""
    default: str = ""
    choices: tuple[str, ...] | None = None


def main() -> None:
    st.set_page_config(page_title="KMA API Debug", layout="wide")
    st.title("KMA API Debug")

    source = st.sidebar.selectbox("Data source", ["datagokr", "apihub"], key="source")
    rows = _catalog_rows(source)
    selected = _select_api(source, rows)

    line1, line2 = _api_summary_lines(selected)
    st.sidebar.caption(line1)
    st.sidebar.caption(line2)

    env_names = env_names_for_gateway(selected.gateway)
    env_sources = _env_key_sources(env_names)

    environment = "manual"
    if env_sources:
        st.sidebar.subheader("Environment")
        environment = st.sidebar.selectbox(
            "Environment", ["env", "manual"], key=f"env-mode:{source}"
        )
        if environment == "env":
            source_info = env_sources[0]
            st.sidebar.caption(
                f"{source_info['name']} 값을 사용합니다. Source: {source_info['source']}"
            )

    st.sidebar.subheader("Auth")
    if environment == "manual":
        api_key = st.sidebar.text_input(
            selected.credential_param,
            value="",
            type="password",
            placeholder="직접 입력",
            help=f"사용 가능한 env 이름: {', '.join(env_names)}",
            key=f"auth:{source}",
        )
        effective_api_key = api_key
    else:
        effective_api_key = _default_key(selected.gateway)
    _service_key_links(selected)

    timeout = st.sidebar.number_input(
        "Timeout",
        min_value=1.0,
        max_value=60.0,
        value=10.0,
        step=1.0,
        help="API 요청 timeout seconds입니다.",
    )
    fixture_base_dir = _fixture_base_dir_sidebar()

    tabs = st.tabs(
        [
            "Raw Response",
            "Pydantic Model",
            "Processed Result",
            "Validation Errors",
            "Debug Trace",
            "Fixture / Testcase",
        ]
    )

    with tabs[0]:
        _raw_response_tab(selected, effective_api_key, timeout=float(timeout))
    with tabs[1]:
        _pydantic_model_tab(selected)
    with tabs[2]:
        _processed_result_tab(selected)
    with tabs[3]:
        _validation_errors_tab(selected)
    with tabs[4]:
        _debug_trace_tab(rows, selected, env_names)
    with tabs[5]:
        _fixture_tab(fixture_base_dir, selected)


def _catalog_rows(source: str) -> tuple[ApiCatalogEntry, ...]:
    """선택한 gateway의 카탈로그 row를 반환합니다.

    `datagokr`는 `api_catalog(gateway="datagokr")`(160개 operation),
    `apihub`는 `apihub_endpoint_catalog()`(470개 실제 호출 가능 endpoint)를
    씁니다 — data.go.kr에 등록만 되어 있고 실행 불가능한 apihub LINK placeholder
    dataset(`api_catalog(gateway="apihub")`)는 이 디버그 UI에서 쓰지 않습니다.
    """

    if source == "apihub":
        return apihub_endpoint_catalog()
    return api_catalog(gateway="datagokr")


def _select_api(source: str, rows: tuple[ApiCatalogEntry, ...]) -> ApiCatalogEntry:
    """Category -> API 2단 계단식 selectbox로 카탈로그 row 하나를 고릅니다.

    `datagokr`는 Category=dataset명(38개), API=operation(160개 중 일부)이고,
    `apihub`는 Category=관측/예특보 등 category명(11개), API=service/endpoint
    제목(470개 중 일부)입니다. 두 gateway 모두 Data source까지 합쳐 3단
    계단식이 됩니다.
    """

    categories = sorted({row.dataset_name for row in rows})
    category = st.sidebar.selectbox("Category", categories, key=f"category:{source}")
    category_rows = [row for row in rows if row.dataset_name == category]
    api_labels = [_api_option_label(source, row) for row in category_rows]
    api_label = st.sidebar.selectbox("API", api_labels, key=f"api:{source}:{category}")
    return category_rows[api_labels.index(api_label)]


def _api_option_label(source: str, row: ApiCatalogEntry) -> str:
    if source == "datagokr":
        return row.operation or row.label
    return row.label


def _api_summary_lines(selected: ApiCatalogEntry) -> tuple[str, str]:
    """사이드바에 표시할 2줄 설명(무엇을 하는 API + 어떤 데이터를 반환하는지)."""

    if selected.gateway == "datagokr":
        line1 = (
            f"{selected.dataset_name} — data.go.kr {selected.service}/{selected.operation} "
            "operation을 호출합니다."
        )
        required = ", ".join(selected.required_params) or "로컬에 정리된 필수 파라미터 없음"
        line2 = f"반환: JSON/XML 응답의 items.item 목록입니다. 필수 파라미터: {required}."
        return line1, line2

    line1 = f"{selected.dataset_name} — APIHub {selected.service}({selected.endpoint_path}) 호출."
    line2 = _RESPONSE_KIND_DESCRIPTIONS.get(
        selected.response_kind, "알 수 없는 형식의 응답입니다."
    )
    return line1, line2


def _raw_response_tab(selected: ApiCatalogEntry, api_key: str, *, timeout: float) -> None:
    st.subheader(selected.dataset_name)
    st.caption(f"{selected.gateway} / {selected.label}")

    try:
        submitted, params, request_options, missing = _request_form(selected)
    except ValueError as exc:
        st.error(str(exc))
        return

    preview: dict[str, Any] = dict(params)
    if selected.gateway == "datagokr":
        preview.update(
            {
                "pageNo": request_options["page_no"],
                "numOfRows": request_options["num_of_rows"],
                "dataType": request_options["data_type"],
            }
        )
    st.subheader("Request params preview")
    st.json(preview)

    if not submitted:
        return
    if missing:
        st.error("필수 파라미터를 입력하세요: " + ", ".join(missing))
        return

    run = _run_selected_api(selected, api_key, params, request_options, timeout=timeout)
    _store_run(selected, run)
    if run.error:
        st.error(run.error["message"])
    st.json(jsonable(run.response))


def _run_selected_api(
    selected: ApiCatalogEntry,
    api_key: str,
    params: dict[str, Any],
    request_options: dict[str, Any],
    *,
    timeout: float,
) -> DebugRun:
    """카탈로그 entry를 gateway에 맞는 클라이언트로 라우팅해 실행합니다.

    endpoint별로 분기하는 코드는 없습니다 — `gateway`(datagokr/apihub) 두
    값으로만 client 클래스를 고르고, 그 다음은 각 client의 제네릭
    `debug_fetch`/`debug_fetch_endpoint`가 `selected.service`/`.operation`
    이름으로 카탈로그 라우팅을 계속합니다. client 생성 자체가 실패해도(예:
    빈 인증값) 구조화된 `DebugRun.error`로 반환합니다.
    """

    try:
        if selected.gateway == "datagokr":
            client = DataGoKrClient(api_key, timeout=timeout, retries=0)
            return client.debug_fetch(
                selected.service or "",
                selected.operation or "",
                params,
                page_no=request_options.get("page_no", 1),
                num_of_rows=request_options.get("num_of_rows", 10),
                data_type=request_options.get("data_type", "JSON"),
            )
        hub_client = ApiHubGeneratedClient(api_key, timeout=timeout, retries=0)
        spec = hub_client.endpoint(selected.service or "")
        return hub_client.debug_fetch_endpoint(spec, params)
    except Exception as exc:  # pragma: no cover - UI 표시
        return DebugRun(
            function=selected.service or selected.label,
            input=redact_sensitive(
                {
                    "gateway": selected.gateway,
                    "service": selected.service,
                    "operation": selected.operation,
                    "params": params,
                }
            ),
            request={},
            response={},
            parsed=None,
            processed=None,
            trace=[f"{selected.gateway} 클라이언트 준비 실패: {exc.__class__.__name__}"],
            error=debug_error(exc),
        )


def _request_form(
    selected: ApiCatalogEntry,
) -> tuple[bool, dict[str, Any], dict[str, Any], list[str]]:
    specs = _parameter_specs(selected)
    required_specs = [spec for spec in specs if spec.required]
    optional_specs = [spec for spec in specs if not spec.required]
    key_prefix = f"{selected.gateway}:{selected.dataset_id}:{selected.service}:{selected.operation}"

    with st.form(f"request-form:{key_prefix}"):
        st.subheader("Required parameters")
        if required_specs:
            required_values = _render_param_grid(required_specs, key_prefix=key_prefix)
        else:
            st.caption(
                "이 API에 대해 로컬에 정리된 필수 파라미터 명세가 없습니다. "
                "Extra params JSON으로 파라미터를 직접 추가하세요."
            )
            required_values = {}

        st.subheader("Optional parameters")
        if optional_specs:
            optional_values = _render_param_grid(optional_specs, key_prefix=key_prefix)
        else:
            st.caption("정리된 선택 파라미터가 없습니다.")
            optional_values = {}

        request_options: dict[str, Any] = {}
        if selected.gateway == "datagokr":
            page_no, num_of_rows, data_type = _render_common_options(key_prefix)
            request_options = {
                "page_no": page_no,
                "num_of_rows": num_of_rows,
                "data_type": data_type,
            }

        extra_text = st.text_area(
            "Extra params JSON",
            value="{}",
            height=110,
            help="폼에 없는 provider 파라미터를 JSON object로 추가합니다.",
            key=f"{key_prefix}:extra",
        )
        submitted = st.form_submit_button("Run selected API")

    params = {**required_values, **optional_values, **_parse_extra_params(extra_text)}
    missing = [spec.name for spec in required_specs if not str(params.get(spec.name, "")).strip()]
    clean_params = {key: value for key, value in params.items() if str(value).strip()}
    return submitted, clean_params, request_options, missing


def _parameter_specs(selected: ApiCatalogEntry) -> tuple[ParameterSpec, ...]:
    """카탈로그의 `required_params`/`optional_params`에서 위젯 명세를 만듭니다.

    `if function_name == ...` 같은 endpoint별 분기는 없습니다 — 파라미터
    이름과 `param_defaults`/enum choices만으로 위젯을 결정합니다.
    """

    defaults = selected.param_defaults
    required = tuple(
        _param(name, required=True, default=defaults.get(name, ""))
        for name in selected.required_params
    )
    optional = tuple(
        _param(name, required=False, default=defaults.get(name, ""))
        for name in selected.optional_params
    )
    return required + optional


def _param(name: str, *, required: bool, default: str) -> ParameterSpec:
    help_text = (
        "이 API의 필수 요청 파라미터입니다." if required else "이 API의 선택 요청 파라미터입니다."
    )
    return ParameterSpec(
        name=name,
        required=required,
        label=name,
        help=help_text,
        default=default,
        choices=_ENUM_CHOICES.get(name),
    )


def _render_param_grid(specs: list[ParameterSpec], *, key_prefix: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for index in range(0, len(specs), 2):
        columns = st.columns(2)
        for column, spec in zip(columns, specs[index : index + 2], strict=False):
            with column:
                if spec.choices:
                    default_index = (
                        spec.choices.index(spec.default) if spec.default in spec.choices else 0
                    )
                    values[spec.name] = st.selectbox(
                        spec.label,
                        spec.choices,
                        index=default_index,
                        help=spec.help or None,
                        key=f"{key_prefix}:param:{spec.name}",
                    )
                else:
                    values[spec.name] = st.text_input(
                        spec.label,
                        value=spec.default,
                        help=spec.help or None,
                        key=f"{key_prefix}:param:{spec.name}",
                    )
    return values


def _render_common_options(key_prefix: str) -> tuple[int, int, str]:
    col1, col2, col3 = st.columns(3)
    with col1:
        page_no = st.number_input(
            "pageNo",
            min_value=1,
            value=1,
            step=1,
            help="공공데이터포털 paging 파라미터입니다.",
            key=f"{key_prefix}:pageNo",
        )
    with col2:
        num_of_rows = st.number_input(
            "numOfRows",
            min_value=1,
            value=10,
            step=1,
            help="한 페이지에 받을 row 수입니다.",
            key=f"{key_prefix}:numOfRows",
        )
    with col3:
        data_type = st.selectbox(
            "dataType",
            ["JSON", "XML"],
            index=0,
            help="기본값은 JSON입니다.",
            key=f"{key_prefix}:dataType",
        )
    return int(page_no), int(num_of_rows), str(data_type)


def _parse_extra_params(text: str) -> dict[str, Any]:
    try:
        payload = json.loads(text or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"Extra params JSON is invalid: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Extra params JSON must be an object")
    reserved = {
        "serviceKey",
        "ServiceKey",
        "authKey",
        "AuthKey",
        "pageNo",
        "numOfRows",
        "dataType",
    }
    return {key: value for key, value in payload.items() if key not in reserved}


def _pydantic_model_tab(selected: ApiCatalogEntry) -> None:
    run = _current_run(selected)
    if run is None:
        st.info("Raw Response 탭에서 선택한 API를 실행하면 여기에서 Pydantic 모델을 확인합니다.")
        return
    if run.error:
        st.warning("실행 중 오류가 있습니다. Validation Errors 탭을 확인하세요.")
    if selected.gateway == "apihub":
        st.caption(
            "APIHub는 endpoint마다 응답 형식(text/structured/image/file)이 달라 전용 "
            "Pydantic row 모델이 없습니다. response_kind에 맞춰 정리한 구조를 표시합니다."
        )
    else:
        st.caption("각 row를 `DataGoKrItem` Pydantic 모델로 검증한 결과입니다.")
    st.json(jsonable(run.parsed))


def _processed_result_tab(selected: ApiCatalogEntry) -> None:
    run = _current_run(selected)
    if run is None:
        st.info("Raw Response 탭에서 API를 실행하면 처리된 row preview를 표시합니다.")
        return
    data = jsonable(run.processed)
    if isinstance(data, list) and data:
        st.dataframe(pd.json_normalize(data, sep="."), width="stretch", hide_index=True)
    else:
        st.json(data)


def _validation_errors_tab(selected: ApiCatalogEntry) -> None:
    run = _current_run(selected)
    if run is None:
        st.info("아직 실행된 API가 없습니다.")
        return
    if not run.error:
        st.success("현재 실행 결과에서 validation error 또는 exception이 없습니다.")
        return
    st.error(run.error["message"])
    st.json(run.error)


def _debug_trace_tab(
    rows: tuple[ApiCatalogEntry, ...],
    selected: ApiCatalogEntry,
    env_names: tuple[str, ...],
) -> None:
    run = _current_run(selected)

    st.subheader("Catalog")
    st.caption(f"현재 Data source 카탈로그: {len(rows)}개 API")
    st.dataframe([row.asdict() for row in rows], width="stretch", hide_index=True)

    st.subheader("Selected API")
    st.json(selected.asdict())
    st.link_button(f"{selected.credential_param} 발급/확인", selected.service_key_url)
    st.caption(f"credential env: {', '.join(env_names)}")

    if run is not None:
        st.subheader("Trace")
        st.write(run.trace)
        st.subheader("Request (redacted)")
        st.json(jsonable(run.request))


def _fixture_tab(fixture_base_dir: str, selected: ApiCatalogEntry) -> None:
    run = _current_run(selected)
    if run is None:
        st.info("Raw Response 탭에서 API를 실행한 뒤 fixture를 저장할 수 있습니다.")
        st.caption("Fixture base dir")
        st.code(fixture_base_dir, language=None)
        return

    with st.expander("Save as fixture", expanded=True):
        case_name = st.text_input("Case name", value=f"{run.function}_normal")
        description = st.text_area("Description", value=f"{selected.label} 정상 케이스")
        assertion_mode = st.selectbox(
            "Assertion mode",
            ["snapshot", "schema_only", "required_fields", "count"],
        )
        exclude_fields_raw = st.text_input(
            "Exclude fields",
            value="fetched_at, collected_at, request_id, updated_at",
        )
        required_fields_raw = st.text_input("Required fields", value="")
        overwrite = st.checkbox("Overwrite existing fixture", value=False)

        assertion = {
            "mode": assertion_mode,
            "exclude_fields": [
                value.strip() for value in exclude_fields_raw.split(",") if value.strip()
            ],
            "required_fields": [
                value.strip() for value in required_fields_raw.split(",") if value.strip()
            ],
        }

        st.subheader("Fixture preview")
        st.json(
            {
                "function": run.function,
                "input": jsonable(run.input),
                "request": jsonable(run.request),
                "response": jsonable(run.response),
                "processed": jsonable(run.processed),
                "assertion": assertion,
            }
        )

        if st.button("Save as fixture"):
            try:
                path = save_fixture(
                    base_dir=fixture_base_dir,
                    function_name=run.function,
                    case_name=case_name,
                    description=description,
                    input_data=run.input,
                    request_data=run.request,
                    response_data=run.response,
                    parsed_result=run.parsed,
                    processed_result=run.processed,
                    assertion=assertion,
                    overwrite=overwrite,
                )
            except Exception as exc:  # pragma: no cover - UI 표시
                st.error(str(exc))
            else:
                st.success(f"Saved: {path}")


def _service_key_links(selected: ApiCatalogEntry) -> None:
    st.sidebar.caption("Service key links")
    st.sidebar.link_button(f"{selected.credential_param} 발급/확인", selected.service_key_url)
    if selected.portal_url != selected.service_key_url:
        st.sidebar.link_button("data.go.kr 카탈로그", selected.portal_url)


def _env_key_sources(env_names: tuple[str, ...]) -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []
    for name in env_names:
        value = os.getenv(name)
        if value is not None and value.strip():
            sources.append({"name": name, "source": "process env"})
            return sources

    local_env = load_local_env()
    for name in env_names:
        value = local_env.get(name)
        if value is not None and value.strip():
            sources.append({"name": name, "source": ".env 또는 .env.local"})
            return sources
    return sources


def _default_key(gateway: str) -> str:
    try:
        return api_key_for_gateway(gateway)
    except ValueError:
        return ""


def _fixture_base_dir_sidebar() -> str:
    st.sidebar.subheader("Fixtures")
    candidates = _fixture_dir_candidates()
    options = [str(path) for path in candidates]
    custom_label = "Custom..."
    selected = st.sidebar.selectbox("Fixture base dir", [*options, custom_label])
    if selected == custom_label:
        selected = st.sidebar.text_input(
            "Custom fixture base dir",
            value=str((ROOT / "tests" / "fixtures").resolve()),
        )
    st.sidebar.caption(selected)
    return selected


def _fixture_dir_candidates() -> list[Path]:
    preferred = [
        ROOT / "tests" / "fixtures",
        ROOT / "tests",
        ROOT / "examples",
        ROOT,
    ]
    candidates: list[Path] = []
    for path in preferred:
        resolved = path.resolve()
        if resolved not in candidates:
            candidates.append(resolved)
    return candidates


def _store_run(selected: ApiCatalogEntry, run: DebugRun) -> None:
    st.session_state["last_run"] = {
        "selection_key": _selection_key(selected),
        "run": run,
    }


def _current_run(selected: ApiCatalogEntry) -> DebugRun | None:
    stored = st.session_state.get("last_run")
    if not isinstance(stored, dict):
        return None
    if stored.get("selection_key") != _selection_key(selected):
        return None
    return stored.get("run")


def _selection_key(selected: ApiCatalogEntry) -> str:
    return f"{selected.gateway}:{selected.dataset_id}:{selected.service}:{selected.operation}"


if __name__ == "__main__":
    main()
