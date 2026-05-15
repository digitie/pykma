"""기상청 API 카탈로그를 UI와 디버깅 도구에서 쓰기 쉬운 row로 제공합니다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .datagokr_catalog import KMA_DATA_GOKR_DATASETS

APIHUB_AUTH_KEY_URL = "https://apihub.kma.go.kr"


@dataclass(frozen=True)
class ApiCatalogEntry:
    """data.go.kr dataset 카탈로그를 operation 단위로 펼친 항목."""

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
    )
