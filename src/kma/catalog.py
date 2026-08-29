"""기상청 API 카탈로그를 UI와 디버깅 도구에서 쓰기 쉬운 row로 제공합니다."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

from .datagokr_catalog import KMA_DATA_GOKR_DATASETS

APIHUB_AUTH_KEY_URL = "https://apihub.kma.go.kr"


@lru_cache(maxsize=1)
def _apihub_openapi_paths() -> frozenset[str]:
    """APIHub `typ02/openApi` wrapper의 path 집합을 반환합니다 (1회 캐시).

    data.go.kr `{service}/{operation}`이 APIHub에도 같은 `typ02/openApi` path로
    존재하는지 판정하는 데 씁니다. 무거운 generated 모듈을 import-time이 아니라
    호출 시점에 lazy load 해 import 순서 의존을 피합니다.
    """

    from .apihub_endpoints import APIHUB_ENDPOINTS

    return frozenset(endpoint.path for endpoint in APIHUB_ENDPOINTS)


def _apihub_equivalent_path(gateway: str, service: str | None, operation: str | None) -> str | None:
    """data.go.kr operation에 대응하는 APIHub `typ02/openApi` path를 반환합니다."""

    if gateway != "datagokr" or not service or not operation:
        return None
    candidate = f"/api/typ02/openApi/{service.strip('/')}/{operation.strip('/')}"
    return candidate if candidate in _apihub_openapi_paths() else None


@dataclass(frozen=True)
class ApiCatalogEntry:
    """data.go.kr dataset 카탈로그를 operation 단위로 펼친 항목.

    `required_params`/`optional_params`는 디버그 UI가 `st.form()` 위젯을
    자동으로 만드는 데 쓰는 파라미터 이름 메타데이터입니다. 로컬에 정리된
    명세가 없는 operation은 두 값 모두 빈 tuple이며, 호출자는 자유 형식
    "Extra params JSON" 입력으로 파라미터를 보충해야 합니다.
    """

    dataset_id: str
    dataset_name: str
    gateway: str
    service: str | None
    operation: str | None
    portal_url: str
    service_key_url: str
    credential_param: str
    page: int
    label: str
    has_apihub_equivalent: bool = False
    apihub_equivalent_path: str | None = None
    required_params: tuple[str, ...] = ()
    optional_params: tuple[str, ...] = ()
    param_defaults: Mapping[str, str] = field(default_factory=dict)
    response_kind: str = "structured"
    endpoint_path: str | None = None

    def asdict(self) -> dict[str, Any]:
        """Streamlit, JSON, 표 렌더링에서 쓰기 쉬운 dict로 변환합니다."""

        return {
            "dataset_id": self.dataset_id,
            "dataset_name": self.dataset_name,
            "gateway": self.gateway,
            "service": self.service,
            "operation": self.operation,
            "portal_url": self.portal_url,
            "service_key_url": self.service_key_url,
            "credential_param": self.credential_param,
            "page": self.page,
            "label": self.label,
            "has_apihub_equivalent": self.has_apihub_equivalent,
            "apihub_equivalent_path": self.apihub_equivalent_path,
            "required_params": list(self.required_params),
            "optional_params": list(self.optional_params),
            "param_defaults": dict(self.param_defaults),
            "response_kind": self.response_kind,
            "endpoint_path": self.endpoint_path,
        }


def api_catalog(
    *,
    gateway: str | None = None,
    dataset_id: str | int | None = None,
) -> tuple[ApiCatalogEntry, ...]:
    """기상청 API 카탈로그를 human-readable dataset 이름이 있는 row로 반환합니다.

    data.go.kr gateway 항목은 operation별로 한 줄씩 펼치고, APIHub LINK 항목은
    dataset 단위 한 줄로 반환합니다. `dataset_name`은 사용자가 읽는 데이터셋명,
    `label`은 UI 선택 목록에 바로 쓸 수 있는 표시 문자열입니다.

    `service_key_url`은 data.go.kr `serviceKey` 또는 APIHub `authKey`를 발급,
    확인할 수 있는 포털 링크입니다.

    이 함수는 data.go.kr 카탈로그(operation 단위)만 다룹니다. APIHub의 470개
    실제 호출 가능 endpoint는 :func:`apihub_endpoint_catalog`가 별도로
    반환합니다 — 서로 다른 두 소스(data.go.kr 카탈로그 vs
    `apiList.do`/`generateAPIUrl.do` 스크래핑 결과)를 섞으면 기존 dataset
    단위 카운트가 흔들리기 때문입니다.
    """

    clean_gateway = gateway.strip().lower() if gateway is not None else None
    clean_dataset_id = str(dataset_id).strip() if dataset_id is not None else None
    rows: list[ApiCatalogEntry] = []
    for dataset in KMA_DATA_GOKR_DATASETS:
        if clean_gateway is not None and dataset.gateway != clean_gateway:
            continue
        if clean_dataset_id is not None and dataset.dataset_id != clean_dataset_id:
            continue

        if dataset.operations:
            for operation in dataset.operations:
                rows.append(_catalog_entry(dataset, operation=operation))
        else:
            rows.append(_catalog_entry(dataset, operation=None))
    return tuple(rows)


def _catalog_entry(dataset: Any, *, operation: str | None) -> ApiCatalogEntry:
    label = dataset.title if operation is None else f"{dataset.title} / {operation}"
    credential_param = "serviceKey" if dataset.gateway == "datagokr" else "authKey"
    service_key_url = dataset.portal_url if dataset.gateway == "datagokr" else APIHUB_AUTH_KEY_URL
    apihub_path = _apihub_equivalent_path(dataset.gateway, dataset.service, operation)
    required_params, optional_params, param_defaults = _datagokr_param_spec(
        dataset.service, operation
    )
    endpoint_path = (
        f"/{dataset.service}/{operation}"
        if dataset.gateway == "datagokr" and dataset.service and operation
        else None
    )
    return ApiCatalogEntry(
        dataset_id=dataset.dataset_id,
        dataset_name=dataset.title,
        gateway=dataset.gateway,
        service=dataset.service,
        operation=operation,
        portal_url=dataset.portal_url,
        service_key_url=service_key_url,
        credential_param=credential_param,
        page=dataset.page,
        label=label,
        has_apihub_equivalent=apihub_path is not None,
        apihub_equivalent_path=apihub_path,
        required_params=required_params,
        optional_params=optional_params,
        param_defaults=param_defaults,
        response_kind="structured",
        endpoint_path=endpoint_path,
    )


def apihub_endpoint_catalog() -> tuple[ApiCatalogEntry, ...]:
    """APIHub `apiList.do`/`generateAPIUrl.do`에서 수집한 470개 실제 호출
    가능 endpoint를 `ApiCatalogEntry` row로 반환합니다.

    각 row의 `service`는 `ApiHubGeneratedClient.call_endpoint(name, ...)`가
    받는 endpoint 식별자(`ApiHubEndpointSpec.name`)입니다. `optional_params`는
    `authKey`를 제외한 그 endpoint의 모든 알려진 query parameter 이름이고,
    `param_defaults`는 `apiList.do`에서 실제로 관찰된 sample 값입니다 — 이
    카탈로그는 어떤 parameter가 진짜 필수인지 표기하지 않으므로(원본 문서에
    없음) 전부 optional로 두고 sample 값으로 미리 채워 실행 가능하게 합니다.
    """

    from .apihub_endpoints import APIHUB_ENDPOINTS

    rows: list[ApiCatalogEntry] = []
    for spec in APIHUB_ENDPOINTS:
        optional_params = tuple(name for name in spec.parameters if name != "authKey")
        rows.append(
            ApiCatalogEntry(
                dataset_id=spec.name,
                dataset_name=spec.category_name,
                gateway="apihub",
                service=spec.name,
                operation=spec.title,
                portal_url=APIHUB_AUTH_KEY_URL,
                service_key_url=APIHUB_AUTH_KEY_URL,
                credential_param="authKey",
                page=spec.category_id,
                label=f"{spec.service_name} / {spec.title}",
                has_apihub_equivalent=False,
                apihub_equivalent_path=None,
                required_params=(),
                optional_params=optional_params,
                param_defaults=dict(spec.sample_params),
                response_kind=spec.response_kind,
                endpoint_path=spec.path,
            )
        )
    return tuple(rows)


def _datagokr_param_spec(
    service: str | None, operation: str | None
) -> tuple[tuple[str, ...], tuple[str, ...], dict[str, str]]:
    """`(service, operation)`에 로컬로 정리된 파라미터 명세가 있으면 반환합니다.

    명세가 없으면 `((), (), {})`를 반환합니다 — 디버그 UI는 이 경우 "Extra
    params JSON" 자유 입력으로 파라미터를 보충하도록 안내합니다. 시간에 따라
    달라지는 값(base_date/tmFc 등)은 기본값을 채우지 않고, 안정적인 코드성
    값(dataCd, regId 등)만 `param_defaults`로 제공합니다.
    """

    spec = _DATAGOKR_PARAM_SPECS.get((service, operation))
    if spec is None:
        return (), (), {}
    required, optional, defaults = spec
    return required, optional, dict(defaults)


# service/operation 조합별 파라미터 명세. 값은 (required, optional, static_defaults)다.
# `static_defaults`는 시간에 의존하지 않는 안정적인 코드 값만 담는다 — base_date,
# base_time, tmFc, currentDate 같은 시각 기반 값은 사용자가 직접 입력한다.
_ParamSpec = tuple[tuple[str, ...], tuple[str, ...], dict[str, str]]
_DATAGOKR_PARAM_SPECS: dict[tuple[str | None, str | None], _ParamSpec] = {
    ("VilageFcstInfoService_2.0", "getUltraSrtNcst"): (
        ("base_date", "base_time", "nx", "ny"),
        (),
        {},
    ),
    ("VilageFcstInfoService_2.0", "getUltraSrtFcst"): (
        ("base_date", "base_time", "nx", "ny"),
        (),
        {},
    ),
    ("VilageFcstInfoService_2.0", "getVilageFcst"): (
        ("base_date", "base_time", "nx", "ny"),
        (),
        {},
    ),
    ("VilageFcstInfoService_2.0", "getFcstVersion"): (
        ("ftype", "basedatetime"),
        (),
        {"ftype": "ODAM"},
    ),
    ("MidFcstInfoService", "getMidFcst"): (
        ("stnId", "tmFc"),
        (),
        {"stnId": "108"},
    ),
    ("MidFcstInfoService", "getMidLandFcst"): (
        ("regId", "tmFc"),
        (),
        {"regId": "11B00000"},
    ),
    ("MidFcstInfoService", "getMidTa"): (
        ("regId", "tmFc"),
        (),
        {"regId": "11B10101"},
    ),
    ("MidFcstInfoService", "getMidSeaFcst"): (
        ("regId", "tmFc"),
        (),
        {"regId": "11B00000"},
    ),
    ("AsosDalyInfoService", "getWthrDataList"): (
        ("startDt", "endDt", "dataCd", "dateCd"),
        ("stnIds",),
        {"dataCd": "ASOS", "dateCd": "DAY"},
    ),
    ("AsosHourlyInfoService", "getWthrDataList"): (
        ("startDt", "startHh", "endDt", "endHh", "dataCd", "dateCd"),
        ("stnIds",),
        {"dataCd": "ASOS", "dateCd": "HR"},
    ),
    ("WthrWrnInfoService", "getWthrWrnList"): (
        ("stnId", "fromTmFc", "toTmFc"),
        (),
        {"stnId": "108"},
    ),
    ("TourStnInfoService1", "getTourStnVilageFcst1"): (
        ("courseId", "currentDate", "hour"),
        (),
        {"courseId": "1"},
    ),
    ("TourStnInfoService1", "getCityTourClmIdx1"): (
        ("cityAreaId", "currentDate", "day"),
        (),
        {"cityAreaId": "1", "day": "0"},
    ),
    ("VilageFcstMsgService", "getWthrSituation"): (
        ("stnId",),
        (),
        {"stnId": "108"},
    ),
    ("VilageFcstMsgService", "getLandFcst"): (
        ("regId",),
        (),
        {"regId": "11B00000"},
    ),
    ("VilageFcstMsgService", "getSeaFcst"): (
        ("regId",),
        (),
        {"regId": "11B00000"},
    ),
    ("BeachInfoservice", "getUltraSrtFcstBeach"): (
        ("beach_num", "base_date", "base_time"),
        (),
        {"beach_num": "1"},
    ),
    ("BeachInfoservice", "getVilageFcstBeach"): (
        ("beach_num", "base_date", "base_time"),
        (),
        {"beach_num": "1"},
    ),
    ("BeachInfoservice", "getWhBuoyBeach"): (
        ("beach_num", "searchTime"),
        (),
        {"beach_num": "1"},
    ),
    ("BeachInfoservice", "getTwBuoyBeach"): (
        ("beach_num", "searchTime"),
        (),
        {"beach_num": "1"},
    ),
    ("BeachInfoservice", "getSunInfoBeach"): (
        ("beach_num", "Base_date"),
        (),
        {"beach_num": "1"},
    ),
    ("BeachInfoservice", "getTideInfoBeach"): (
        ("beach_num", "base_date"),
        (),
        {"beach_num": "1"},
    ),
    ("LivingWthrIdxServiceV4", "getSenTaIdxV4"): (
        ("areaNo", "time", "requestCode"),
        (),
        {"areaNo": "1100000000", "requestCode": "A01"},
    ),
    ("LivingWthrIdxServiceV4", "getUVIdxV4"): (
        ("areaNo", "time"),
        (),
        {"areaNo": "1100000000"},
    ),
    ("LivingWthrIdxServiceV4", "getAirDiffusionIdxV4"): (
        ("areaNo", "time"),
        (),
        {"areaNo": "1100000000"},
    ),
    ("EqkInfoService", "getEqkMsg"): (("fromTmFc", "toTmFc"), (), {}),
    ("EqkInfoService", "getEqkMsgList"): (("fromTmFc", "toTmFc"), (), {}),
    ("EqkInfoService", "getTsunamiMsg"): (("fromTmFc", "toTmFc"), (), {}),
    ("EqkInfoService", "getTsunamiMsgList"): (("fromTmFc", "toTmFc"), (), {}),
}
