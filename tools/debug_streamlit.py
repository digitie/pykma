"""Streamlit 기반 KMA API 디버그 카탈로그 뷰어."""
# ruff: noqa: E402,I001

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
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
    import streamlit as st
except ModuleNotFoundError as exc:  # pragma: no cover - 선택 실행 도구
    raise SystemExit('Streamlit UI를 쓰려면 `pip install -e ".[debug-ui]"`를 실행하세요.') from exc

from kma import (  # noqa: E402
    DataGoKrClient,
    DataGoKrItem,
    MidForecastItem,
    api_catalog,
    api_key_for_gateway,
    env_names_for_gateway,
    load_local_env,
)
from kma.time_utils import (  # noqa: E402
    KST,
    latest_mid_fcst_time,
    latest_ultra_srt_fcst_base,
    latest_ultra_srt_ncst_base,
    latest_vilage_base,
)


@dataclass(frozen=True)
class ParameterSpec:
    """디버그 UI에서 요청 파라미터 입력 폼을 만들기 위한 최소 명세."""

    name: str
    required: bool
    label: str
    placeholder: str = ""
    help: str = ""
    default: str = ""


def _param(
    name: str,
    *,
    required: bool = True,
    label: str | None = None,
    placeholder: str = "",
    help: str = "",
    default: str = "",
) -> ParameterSpec:
    return ParameterSpec(
        name=name,
        required=required,
        label=label or name,
        placeholder=placeholder,
        help=help,
        default=default,
    )


_DEFAULT_STATION = "108"
_DEFAULT_GRID_X = "60"
_DEFAULT_GRID_Y = "127"
_DEFAULT_AREA_NO = "1100000000"


def main() -> None:
    st.set_page_config(page_title="KMA API Debug", layout="wide")
    st.title("KMA API Debug")

    source = st.sidebar.selectbox("Data source", ["datagokr", "apihub"])
    rows = list(api_catalog(gateway=source))
    selected_label = st.sidebar.selectbox("API", [row.label for row in rows])
    selected = rows[[row.label for row in rows].index(selected_label)]
    st.sidebar.caption("API full name")
    st.sidebar.write(_api_full_name(selected))
    st.sidebar.caption(_api_description(selected))

    env_names = env_names_for_gateway(selected.gateway)
    default_key = _default_key(selected.gateway)
    env_sources = _env_key_sources(selected.gateway)

    environment = "manual"
    if env_sources:
        st.sidebar.subheader("Environment")
        environment = st.sidebar.selectbox("Environment", ["env", "manual"])
        if environment == "env":
            source_info = env_sources[0]
            st.sidebar.caption(
                f"{source_info['name']} 값을 사용합니다. Source: {source_info['source']}"
            )

    st.sidebar.subheader("Auth")
    if environment == "manual":
        api_key = st.sidebar.text_input(
            f"{selected.credential_param}",
            value="",
            type="password",
            placeholder="직접 입력",
            help=f"사용 가능한 env 이름: {', '.join(env_names)}",
        )
        effective_api_key = api_key
    else:
        effective_api_key = default_key
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
        _fixture_tab(fixture_base_dir)


def _raw_response_tab(selected: Any, api_key: str, *, timeout: float) -> None:
    st.subheader(selected.dataset_name)
    st.caption(f"{selected.gateway} / {selected.service or '-'} / {selected.operation or '-'}")
    if selected.gateway != "datagokr" or not selected.service or not selected.operation:
        st.info("APIHub 연계 항목은 APIHub 함수형 wrapper에서 endpoint를 선택해 호출합니다.")
        return

    try:
        submitted, params, extra_params, request_options, missing = _request_form(selected)
    except ValueError as exc:
        st.error(str(exc))
        return
    preview = {
        **params,
        **extra_params,
        "pageNo": request_options["page_no"],
        "numOfRows": request_options["num_of_rows"],
        "dataType": request_options["data_type"],
    }
    st.subheader("Request params preview")
    st.json(preview)

    if not submitted:
        return
    if missing:
        st.error("필수 파라미터를 입력하세요: " + ", ".join(missing))
        return

    try:
        params.update(extra_params)
        client = DataGoKrClient(api_key, timeout=timeout)
        body = client.request(
            selected.service,
            selected.operation,
            params,
            data_type=request_options["data_type"],
            page_no=request_options["page_no"],
            num_of_rows=request_options["num_of_rows"],
        )
    except Exception as exc:  # pragma: no cover - UI 표시
        _store_run(
            selected,
            body=None,
            request_params=preview,
            model_name=None,
            models=[],
            validation_errors=[str(exc)],
        )
        st.error(str(exc))
        return
    model_name, models, validation_errors = _parse_models(selected, body)
    _store_run(
        selected,
        body=body,
        request_params=preview,
        model_name=model_name,
        models=models,
        validation_errors=validation_errors,
    )
    st.json(body)


def _request_form(
    selected: Any,
) -> tuple[bool, dict[str, Any], dict[str, Any], dict[str, Any], list[str]]:
    specs = _parameter_specs(selected.service, selected.operation)
    required_specs = [spec for spec in specs if spec.required]
    optional_specs = [spec for spec in specs if not spec.required]
    key_prefix = f"{selected.dataset_id}:{selected.service}:{selected.operation}"

    with st.form(f"request-form:{key_prefix}"):
        st.subheader("Required parameters")
        if required_specs:
            required_values = _render_param_grid(required_specs, key_prefix=key_prefix)
        else:
            st.caption("이 API에 대해 로컬에 정리된 필수 파라미터 명세가 없습니다.")
            required_values = {}

        st.subheader("Optional parameters")
        optional_values = _render_param_grid(optional_specs, key_prefix=key_prefix)
        page_no, num_of_rows, data_type = _render_common_options(key_prefix)

        extra_text = st.text_area(
            "Extra params JSON",
            value="{}",
            height=110,
            help="폼에 없는 provider 파라미터를 JSON object로 추가합니다.",
            key=f"{key_prefix}:extra",
        )
        submitted = st.form_submit_button("Run selected API")

    params = {**required_values, **optional_values}
    missing = [spec.name for spec in required_specs if not str(params.get(spec.name, "")).strip()]
    extra_params = _parse_extra_params(extra_text)
    return (
        submitted,
        {key: value for key, value in params.items() if str(value).strip()},
        extra_params,
        {"page_no": page_no, "num_of_rows": num_of_rows, "data_type": data_type},
        missing,
    )


def _render_param_grid(specs: list[ParameterSpec], *, key_prefix: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for index in range(0, len(specs), 2):
        columns = st.columns(2)
        for column, spec in zip(columns, specs[index : index + 2]):
            with column:
                values[spec.name] = st.text_input(
                    spec.label,
                    value=spec.default,
                    placeholder=spec.placeholder,
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
    return {
        key: value
        for key, value in payload.items()
        if key not in {"serviceKey", "ServiceKey", "authKey", "pageNo", "numOfRows", "dataType"}
    }


def _parameter_specs(service: str | None, operation: str | None) -> tuple[ParameterSpec, ...]:
    if not service or not operation:
        return ()
    endpoint = (service, operation)
    if endpoint in _PARAMETER_SPECS:
        return _PARAMETER_SPECS[endpoint]()
    if service == "MidFcstInfoService":
        return _mid_forecast_specs(operation)
    if service == "BeachInfoservice":
        return _beach_specs(operation)
    if service == "VilageFcstMsgService":
        return _forecast_message_specs(operation)
    if service == "LivingWthrIdxServiceV4":
        return _living_weather_specs(operation)
    if service == "EqkInfoService":
        return _date_range_specs()
    return ()


def _short_forecast_specs() -> tuple[ParameterSpec, ...]:
    base_date, base_time = latest_ultra_srt_fcst_base()
    return _base_grid_specs(base_date, base_time)


def _now_specs() -> tuple[ParameterSpec, ...]:
    base_date, base_time = latest_ultra_srt_ncst_base()
    return _base_grid_specs(base_date, base_time)


def _vilage_specs() -> tuple[ParameterSpec, ...]:
    base_date, base_time = latest_vilage_base()
    return _base_grid_specs(base_date, base_time)


def _base_grid_specs(base_date: str, base_time: str) -> tuple[ParameterSpec, ...]:
    return (
        _param("base_date", label="base_date (YYYYMMDD)", default=base_date),
        _param("base_time", label="base_time (HHMM)", default=base_time),
        _param("nx", label="nx", default=_DEFAULT_GRID_X, help="KMA DFS 격자 x입니다."),
        _param("ny", label="ny", default=_DEFAULT_GRID_Y, help="KMA DFS 격자 y입니다."),
    )


def _version_specs() -> tuple[ParameterSpec, ...]:
    return (
        _param("ftype", default="ODAM", help="예보 버전 조회 타입입니다."),
        _param("basedatetime", label="basedatetime (YYYYMMDDHHMM)", default=_now("%Y%m%d%H%M")),
    )


def _mid_forecast_specs(operation: str) -> tuple[ParameterSpec, ...]:
    if operation == "getMidFcst":
        return (
            _param("stnId", default=_DEFAULT_STATION, help="전국 예보 통보문 지점 코드입니다."),
            _param("tmFc", label="tmFc (YYYYMMDDHHMM)", default=latest_mid_fcst_time()),
        )
    default_reg_id = "11B10101" if operation == "getMidTa" else "11B00000"
    return (
        _param("regId", default=default_reg_id, help="중기예보 권역 코드입니다."),
        _param("tmFc", label="tmFc (YYYYMMDDHHMM)", default=latest_mid_fcst_time()),
    )


def _asos_daily_specs() -> tuple[ParameterSpec, ...]:
    today = _now("%Y%m%d")
    return (
        _param("startDt", label="startDt (YYYYMMDD)", default=today),
        _param("endDt", label="endDt (YYYYMMDD)", default=today),
        _param("dataCd", default="ASOS"),
        _param("dateCd", default="DAY"),
        _param("stnIds", required=False, default=_DEFAULT_STATION, help="비우면 전체 지점입니다."),
    )


def _asos_hourly_specs() -> tuple[ParameterSpec, ...]:
    today = _now("%Y%m%d")
    return (
        _param("startDt", label="startDt (YYYYMMDD)", default=today),
        _param("startHh", label="startHh (HH)", default="00"),
        _param("endDt", label="endDt (YYYYMMDD)", default=today),
        _param("endHh", label="endHh (HH)", default="23"),
        _param("dataCd", default="ASOS"),
        _param("dateCd", default="HR"),
        _param("stnIds", required=False, default=_DEFAULT_STATION, help="비우면 전체 지점입니다."),
    )


def _weather_warning_specs() -> tuple[ParameterSpec, ...]:
    today = _now("%Y%m%d")
    return (
        _param("stnId", default=_DEFAULT_STATION),
        _param("fromTmFc", label="fromTmFc (YYYYMMDD)", default=today),
        _param("toTmFc", label="toTmFc (YYYYMMDD)", default=today),
    )


def _forecast_message_specs(operation: str) -> tuple[ParameterSpec, ...]:
    if operation == "getWthrSituation":
        return (_param("stnId", default=_DEFAULT_STATION),)
    if operation in {"getLandFcst", "getSeaFcst"}:
        return (_param("regId", default="11B00000"),)
    return ()


def _beach_specs(operation: str) -> tuple[ParameterSpec, ...]:
    if operation == "getUltraSrtFcstBeach":
        base_date, base_time = latest_ultra_srt_fcst_base()
        return (
            _param("beach_num", default="1", help="해수욕장 코드입니다."),
            _param("base_date", label="base_date (YYYYMMDD)", default=base_date),
            _param("base_time", label="base_time (HHMM)", default=base_time),
        )
    if operation == "getVilageFcstBeach":
        base_date, base_time = latest_vilage_base()
        return (
            _param("beach_num", default="1", help="해수욕장 코드입니다."),
            _param("base_date", label="base_date (YYYYMMDD)", default=base_date),
            _param("base_time", label="base_time (HHMM)", default=base_time),
        )
    if operation in {"getWhBuoyBeach", "getTwBuoyBeach"}:
        return (
            _param("beach_num", default="1", help="해수욕장 코드입니다."),
            _param("searchTime", label="searchTime (YYYYMMDDHHMM)", default=_now("%Y%m%d%H%M")),
        )
    if operation == "getSunInfoBeach":
        return (
            _param("beach_num", default="1", help="해수욕장 코드입니다."),
            _param("Base_date", label="Base_date (YYYYMMDD)", default=_now("%Y%m%d")),
        )
    return (
        _param("beach_num", default="1", help="해수욕장 코드입니다."),
        _param("base_date", label="base_date (YYYYMMDD)", default=_now("%Y%m%d")),
    )


def _tour_village_specs() -> tuple[ParameterSpec, ...]:
    return (
        _param("courseId", default="1"),
        _param("currentDate", label="currentDate (YYYYMMDD)", default=_now("%Y%m%d")),
        _param("hour", label="hour (HH)", default=_now("%H")),
    )


def _city_tour_specs() -> tuple[ParameterSpec, ...]:
    return (
        _param("cityAreaId", default="1"),
        _param("currentDate", label="currentDate (YYYYMMDD)", default=_now("%Y%m%d")),
        _param("day", default="0"),
    )


def _living_weather_specs(operation: str) -> tuple[ParameterSpec, ...]:
    specs = [
        _param("areaNo", default=_DEFAULT_AREA_NO),
        _param("time", label="time (YYYYMMDDHH)", default=_now("%Y%m%d%H")),
    ]
    if operation == "getSenTaIdxV4":
        specs.append(_param("requestCode", default="A01"))
    return tuple(specs)


def _date_range_specs() -> tuple[ParameterSpec, ...]:
    today = _now("%Y%m%d")
    return (
        _param("fromTmFc", label="fromTmFc (YYYYMMDD)", default=today),
        _param("toTmFc", label="toTmFc (YYYYMMDD)", default=today),
    )


def _now(fmt: str) -> str:
    return datetime.now(tz=KST).strftime(fmt)


_PARAMETER_SPECS: dict[tuple[str, str], Any] = {
    ("VilageFcstInfoService_2.0", "getUltraSrtNcst"): _now_specs,
    ("VilageFcstInfoService_2.0", "getUltraSrtFcst"): _short_forecast_specs,
    ("VilageFcstInfoService_2.0", "getVilageFcst"): _vilage_specs,
    ("VilageFcstInfoService_2.0", "getFcstVersion"): _version_specs,
    ("AsosDalyInfoService", "getWthrDataList"): _asos_daily_specs,
    ("AsosHourlyInfoService", "getWthrDataList"): _asos_hourly_specs,
    ("WthrWrnInfoService", "getWthrWrnList"): _weather_warning_specs,
    ("TourStnInfoService1", "getTourStnVilageFcst1"): _tour_village_specs,
    ("TourStnInfoService1", "getCityTourClmIdx1"): _city_tour_specs,
}


def _api_full_name(selected: Any) -> str:
    if selected.service and selected.operation:
        return f"{selected.dataset_name} / {selected.service} / {selected.operation}"
    return f"{selected.dataset_name} / {selected.gateway}"


def _api_description(selected: Any) -> str:
    key = (selected.service, selected.operation)
    if key in _API_DESCRIPTIONS:
        return _API_DESCRIPTIONS[key]
    if selected.gateway == "apihub":
        return "data.go.kr 카탈로그에서 APIHub로 연결되는 기상청 API입니다."
    if selected.operation:
        return f"{selected.dataset_name}의 {selected.operation} operation입니다."
    return f"{selected.dataset_name} API입니다."


_API_DESCRIPTIONS: dict[tuple[str | None, str | None], str] = {
    ("VilageFcstInfoService_2.0", "getUltraSrtNcst"): (
        "초단기실황 관측값을 KMA DFS 격자 기준으로 조회합니다."
    ),
    ("VilageFcstInfoService_2.0", "getUltraSrtFcst"): (
        "초단기예보를 발표시각과 격자 좌표 기준으로 조회합니다."
    ),
    ("VilageFcstInfoService_2.0", "getVilageFcst"): (
        "단기예보를 발표시각과 격자 좌표 기준으로 조회합니다."
    ),
    ("VilageFcstInfoService_2.0", "getFcstVersion"): (
        "예보 데이터의 버전 metadata를 조회합니다."
    ),
    ("MidFcstInfoService", "getMidFcst"): "전국 중기예보 통보문을 조회합니다.",
    ("MidFcstInfoService", "getMidLandFcst"): (
        "중기 육상예보를 권역 코드와 발표시각 기준으로 조회합니다."
    ),
    ("MidFcstInfoService", "getMidTa"): (
        "중기 기온예보를 권역 코드와 발표시각 기준으로 조회합니다."
    ),
    ("MidFcstInfoService", "getMidSeaFcst"): (
        "중기 해상예보를 권역 코드와 발표시각 기준으로 조회합니다."
    ),
    ("AsosDalyInfoService", "getWthrDataList"): (
        "ASOS 지상 관측 일자료를 기간과 지점 기준으로 조회합니다."
    ),
    ("AsosHourlyInfoService", "getWthrDataList"): (
        "ASOS 지상 관측 시간자료를 기간과 지점 기준으로 조회합니다."
    ),
    ("WthrWrnInfoService", "getWthrWrnList"): "기상특보 목록을 지점과 발표일 범위로 조회합니다.",
    ("BeachInfoservice", "getUltraSrtFcstBeach"): (
        "해수욕장 초단기예보를 해변 코드와 발표시각 기준으로 조회합니다."
    ),
    ("BeachInfoservice", "getVilageFcstBeach"): (
        "해수욕장 단기예보를 해변 코드와 발표시각 기준으로 조회합니다."
    ),
    ("BeachInfoservice", "getWhBuoyBeach"): "해수욕장 주변 파고 관측값을 조회합니다.",
    ("BeachInfoservice", "getTideInfoBeach"): "해수욕장 조석 정보를 조회합니다.",
    ("BeachInfoservice", "getSunInfoBeach"): "해수욕장 일출/일몰 정보를 조회합니다.",
    ("BeachInfoservice", "getTwBuoyBeach"): "해수욕장 주변 수온 관측값을 조회합니다.",
}


def _service_key_links(selected: Any) -> None:
    st.sidebar.caption("Service key links")
    st.sidebar.link_button(
        f"{selected.credential_param} 발급/확인",
        selected.service_key_url,
    )
    if selected.portal_url != selected.service_key_url:
        st.sidebar.link_button("data.go.kr 카탈로그", selected.portal_url)


def _env_key_sources(gateway: str) -> list[dict[str, str]]:
    names = env_names_for_gateway(gateway)
    sources: list[dict[str, str]] = []
    for name in names:
        value = os.getenv(name)
        if value is not None and value.strip():
            sources.append({"name": name, "source": "process env"})
            return sources

    local_env = load_local_env()
    for name in names:
        value = local_env.get(name)
        if value is not None and value.strip():
            sources.append({"name": name, "source": ".env 또는 .env.local"})
            return sources
    return sources


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
        ROOT / "tools",
        ROOT,
    ]
    candidates: list[Path] = []
    for path in preferred:
        resolved = path.resolve()
        if resolved not in candidates:
            candidates.append(resolved)
    return candidates


def _pydantic_model_tab(selected: Any) -> None:
    run = _current_run(selected)
    if run is None:
        st.info("Raw Response 탭에서 선택한 API를 실행하면 여기에서 Pydantic 모델을 확인합니다.")
        return
    if run["validation_errors"]:
        st.warning("모델 파싱 중 확인할 내용이 있습니다. Validation Errors 탭을 확인하세요.")
    if not run["models"]:
        st.info("응답에서 `body.items.item` row를 찾지 못해 Pydantic row 모델을 만들지 않았습니다.")
        if run["body"] is not None:
            st.json(run["body"])
        return

    st.caption(f"{run['model_name']} · {len(run['models'])} rows")
    st.json(run["models"])


def _processed_result_tab(selected: Any) -> None:
    run = _current_run(selected)
    if run is None:
        st.info("Raw Response 탭에서 API를 실행하면 처리된 row preview를 표시합니다.")
        return
    if not run["models"]:
        st.info("표시할 처리 결과가 없습니다.")
        return

    rows = [model.get("raw", model) for model in run["models"]]
    st.dataframe(rows, width="stretch", hide_index=True)


def _validation_errors_tab(selected: Any) -> None:
    run = _current_run(selected)
    if run is None:
        st.info("아직 실행된 API가 없습니다.")
        return
    if not run["validation_errors"]:
        st.success("현재 실행 결과에서 validation error가 없습니다.")
        return
    for error in run["validation_errors"]:
        st.error(error)


def _fixture_tab(fixture_base_dir: str) -> None:
    st.info("Fixture 저장 기능은 replay runner와 함께 별도 단계에서 연결합니다.")
    st.caption("Fixture base dir")
    st.code(fixture_base_dir, language=None)


def _parse_models(selected: Any, body: Any) -> tuple[str | None, list[dict[str, Any]], list[str]]:
    try:
        rows = _items_from_body(body)
    except ValueError as exc:
        return None, [], [str(exc)]

    models: list[dict[str, Any]] = []
    errors: list[str] = []
    model_name = "MidForecastItem" if selected.service == "MidFcstInfoService" else "DataGoKrItem"
    for index, row in enumerate(rows):
        try:
            if selected.service == "MidFcstInfoService":
                model = MidForecastItem(
                    operation=str(selected.operation),
                    tm_fc=_str_or_none(row.get("tmFc")),
                    reg_id=_str_or_none(row.get("regId")),
                    stn_id=_str_or_none(row.get("stnId")),
                    raw=dict(row),
                )
            else:
                model = DataGoKrItem(
                    service=str(selected.service),
                    operation=str(selected.operation),
                    raw=dict(row),
                )
            models.append(model.model_dump(mode="json"))
        except Exception as exc:
            errors.append(f"row {index}: {exc}")
    return model_name, models, errors


def _items_from_body(body: Any) -> list[dict[str, Any]]:
    try:
        raw_items = body["items"]["item"]
    except (KeyError, TypeError) as exc:
        raise ValueError("response body does not contain `items.item`") from exc
    if isinstance(raw_items, dict):
        return [raw_items]
    if isinstance(raw_items, list):
        return [dict(item) for item in raw_items if isinstance(item, dict)]
    raise ValueError("response `items.item` is not an object or list")


def _store_run(
    selected: Any,
    *,
    body: Any,
    request_params: dict[str, Any],
    model_name: str | None,
    models: list[dict[str, Any]],
    validation_errors: list[str],
) -> None:
    st.session_state["last_run"] = {
        "selection_key": _selection_key(selected),
        "body": body,
        "request_params": request_params,
        "model_name": model_name,
        "models": models,
        "validation_errors": validation_errors,
    }


def _current_run(selected: Any) -> dict[str, Any] | None:
    run = st.session_state.get("last_run")
    if not isinstance(run, dict):
        return None
    if run.get("selection_key") != _selection_key(selected):
        return None
    return run


def _selection_key(selected: Any) -> str:
    return f"{selected.gateway}:{selected.dataset_id}:{selected.service}:{selected.operation}"


def _str_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _debug_trace_tab(rows: list[Any], selected: Any, env_names: tuple[str, ...]) -> None:
    st.subheader("Catalog")
    st.dataframe(
        [row.asdict() for row in rows],
        width="stretch",
        hide_index=True,
    )

    st.subheader("Selected API")
    st.json(selected.asdict())
    st.link_button(f"{selected.credential_param} 발급/확인", selected.service_key_url)
    st.caption(f"credential env: {', '.join(env_names)}")


def _default_key(gateway: str) -> str:
    try:
        return api_key_for_gateway(gateway)
    except ValueError:
        return ""


if __name__ == "__main__":
    main()
