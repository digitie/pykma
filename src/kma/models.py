"""공개 클라이언트가 반환하는 Pydantic 모델."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from kraddr.base import PlaceCoordinate
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .codes import unit_for
from .enums import WeatherCategory, category_or_none, coerce_category, enum_value
from .locations import GridPoint, LatLon
from .metadata import ResponseMetadata


class kmaModel(BaseModel):
    """불변 공개 `kma` 응답 모델의 기본 클래스."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class WeatherSnapshot(kmaModel):
    observed_at: datetime
    nx: int
    ny: int
    coordinate: PlaceCoordinate | None = None
    temperature: float | None
    humidity: int | None
    wind_speed: float | None
    wind_direction: int | None
    precipitation: float | None
    sky_label: str | None
    precipitation_label: str | None
    raw: dict[str, Any]
    metadata: ResponseMetadata | None = None

    @model_validator(mode="after")
    def _validate_grid(self) -> WeatherSnapshot:
        GridPoint(self.nx, self.ny)
        return self

    @property
    def grid(self) -> GridPoint:
        """이 관측값의 KMA DFS 격자 좌표를 반환합니다."""

        return GridPoint(self.nx, self.ny)

    @property
    def latlon(self) -> LatLon:
        """이 관측값 격자 셀의 근사 WGS84 좌표를 반환합니다."""

        return self.grid.to_latlon()


class ForecastItem(kmaModel):
    base_at: datetime
    forecast_at: datetime
    nx: int
    ny: int
    coordinate: PlaceCoordinate | None = None
    category: WeatherCategory | str
    value: str | float
    label: str | None
    raw: dict[str, Any] = Field(default_factory=dict)
    metadata: ResponseMetadata | None = None

    @field_validator("category", mode="before")
    @classmethod
    def _coerce_category(cls, value: object) -> WeatherCategory | str:
        return coerce_category(value)

    @model_validator(mode="after")
    def _validate_grid(self) -> ForecastItem:
        GridPoint(self.nx, self.ny)
        return self

    @property
    def category_enum(self) -> WeatherCategory | None:
        """알려진 KMA category이면 `WeatherCategory`를 반환합니다."""

        return category_or_none(self.category)

    @property
    def unit(self) -> str | None:
        """알려진 category이면 관례적인 단위를 반환합니다."""

        return unit_for(self.category)

    @property
    def grid(self) -> GridPoint:
        """이 예보 항목의 KMA DFS 격자 좌표를 반환합니다."""

        return GridPoint(self.nx, self.ny)

    @property
    def latlon(self) -> LatLon:
        """이 예보 항목 격자 셀의 근사 WGS84 좌표를 반환합니다."""

        return self.grid.to_latlon()


class ForecastTimepoint(kmaModel):
    """예보 row를 `forecast_at` 기준으로 피벗한 시간대별 예보 묶음."""

    base_at: datetime | None = None
    forecast_at: datetime
    nx: int
    ny: int
    coordinate: PlaceCoordinate | None = None
    values: dict[str, str | float] = Field(default_factory=dict)
    labels: dict[str, str] = Field(default_factory=dict)
    units: dict[str, str] = Field(default_factory=dict)
    raw_items: list[dict[str, Any]] = Field(default_factory=list)
    metadata: ResponseMetadata | None = None

    @model_validator(mode="after")
    def _validate_grid(self) -> ForecastTimepoint:
        GridPoint(self.nx, self.ny)
        return self

    @property
    def grid(self) -> GridPoint:
        """이 시간대 예보의 KMA DFS 격자 좌표를 반환합니다."""

        return GridPoint(self.nx, self.ny)

    @property
    def latlon(self) -> LatLon:
        """이 시간대 예보 격자 셀의 근사 WGS84 좌표를 반환합니다."""

        return self.grid.to_latlon()

    def value(self, category: str | WeatherCategory) -> str | float | None:
        """category code에 해당하는 예보값을 반환합니다."""

        return self.values.get(enum_value(category))

    def label(self, category: str | WeatherCategory) -> str | None:
        """category code에 해당하는 사람이 읽을 수 있는 라벨을 반환합니다."""

        return self.labels.get(enum_value(category))

    def unit(self, category: str | WeatherCategory) -> str | None:
        """category code에 해당하는 관례적 단위를 반환합니다."""

        return self.units.get(enum_value(category))


class DataGoKrItem(kmaModel):
    """endpoint별 전용 모델이 없는 data.go.kr row용 범용 타입 wrapper."""

    service: str
    operation: str
    raw: dict[str, Any]
    metadata: ResponseMetadata | None = None


class BeachForecastItem(kmaModel):
    """`BeachInfoservice` 해수욕장 예보 endpoint의 예보 row."""

    operation: str
    base_at: datetime
    forecast_at: datetime
    beach_num: str
    category: WeatherCategory | str
    value: str | float
    label: str | None
    nx: int | None = None
    ny: int | None = None
    coordinate: PlaceCoordinate | None = None
    raw: dict[str, Any] = Field(default_factory=dict)
    metadata: ResponseMetadata | None = None

    @field_validator("category", mode="before")
    @classmethod
    def _coerce_category(cls, value: object) -> WeatherCategory | str:
        return coerce_category(value)

    @model_validator(mode="after")
    def _validate_optional_grid(self) -> BeachForecastItem:
        if (self.nx is None) != (self.ny is None):
            raise ValueError("nx and ny must be provided together")
        if self.nx is not None and self.ny is not None:
            GridPoint(self.nx, self.ny)
        return self

    @property
    def category_enum(self) -> WeatherCategory | None:
        """알려진 KMA category이면 `WeatherCategory`를 반환합니다."""

        return category_or_none(self.category)

    @property
    def unit(self) -> str | None:
        """알려진 category이면 관례적인 단위를 반환합니다."""

        return unit_for(self.category)

    @property
    def grid(self) -> GridPoint | None:
        """격자 좌표가 있으면 이 예보 항목의 KMA DFS 좌표를 반환합니다."""

        if self.nx is None or self.ny is None:
            return None
        return GridPoint(self.nx, self.ny)

    @property
    def latlon(self) -> LatLon | None:
        """이 예보 항목 격자 셀의 근사 WGS84 좌표를 반환합니다."""

        grid = self.grid
        if grid is None:
            return None
        return grid.to_latlon()


class BeachWaveHeight(kmaModel):
    """`getWhBuoyBeach`의 파고 관측 row."""

    observed_at: datetime
    beach_num: str
    wave_height: float | None
    raw: dict[str, Any]
    metadata: ResponseMetadata | None = None


class BeachWaterTemperature(kmaModel):
    """`getTwBuoyBeach`의 수온 관측 row."""

    observed_at: datetime
    beach_num: str
    water_temperature: float | None
    raw: dict[str, Any]
    metadata: ResponseMetadata | None = None


class BeachTideItem(kmaModel):
    """`getTideInfoBeach`의 조석 row."""

    base_date: str
    beach_num: str
    station_name: str | None
    tide_time: str | None
    tide_type: str | None
    tide_level: float | None
    raw: dict[str, Any]
    metadata: ResponseMetadata | None = None


class BeachSunTime(kmaModel):
    """`getSunInfoBeach`의 일출/일몰 row."""

    base_date: str
    beach_num: str
    sunrise: str | None
    sunset: str | None
    raw: dict[str, Any]
    metadata: ResponseMetadata | None = None


class MidForecastItem(kmaModel):
    """기상청 `MidFcstInfoService` 응답용 타입화 row wrapper.

    `reg_id`는 기상청 중기예보 구역 식별자입니다. 단기예보 `nx`/`ny`
    DFS 격자 좌표와 서로 바꿔 쓸 수 없으며, `kma`는 두 좌표계 사이의
    mapping을 추정하지 않습니다.
    """

    operation: str
    tm_fc: str | None
    reg_id: str | None = None
    stn_id: str | None = None
    raw: dict[str, Any]
    metadata: ResponseMetadata | None = None
