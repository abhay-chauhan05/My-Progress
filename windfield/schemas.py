"""Pydantic request / response models for the wind-field API."""
from __future__ import annotations

from datetime import date as DateType
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class BoundingBox(BaseModel):
    """Geographic area of interest in decimal degrees (WGS84)."""

    lon_min: float = Field(..., ge=-180, le=180, description="Western longitude")
    lat_min: float = Field(..., ge=-90, le=90, description="Southern latitude")
    lon_max: float = Field(..., ge=-180, le=180, description="Eastern longitude")
    lat_max: float = Field(..., ge=-90, le=90, description="Northern latitude")

    @model_validator(mode="after")
    def _check_order(self) -> "BoundingBox":
        if self.lon_min >= self.lon_max:
            raise ValueError("lon_min must be smaller than lon_max")
        if self.lat_min >= self.lat_max:
            raise ValueError("lat_min must be smaller than lat_max")
        # Guard against absurdly large requests.
        if (self.lon_max - self.lon_min) > 6 or (self.lat_max - self.lat_min) > 6:
            raise ValueError("Area of interest too large (max 6 deg per side)")
        return self

    def as_tuple(self) -> tuple[float, float, float, float]:
        return (self.lon_min, self.lat_min, self.lon_max, self.lat_max)


class WindFieldRequest(BaseModel):
    """User request: a date and an area of interest."""

    date: DateType = Field(..., description="Acquisition date (YYYY-MM-DD)")
    bbox: BoundingBox | None = Field(
        default=None, description="Explicit area of interest"
    )
    region: Literal["tamilnadu", "gujarat"] | None = Field(
        default=None, description="Named coastal study-area preset"
    )
    grid_km: float | None = Field(
        default=None, gt=0.2, le=25, description="Spacing of output vectors (km)"
    )
    source: Literal["auto", "synthetic", "copernicus"] | None = Field(
        default=None, description="Override the data source"
    )

    @model_validator(mode="after")
    def _need_area(self) -> "WindFieldRequest":
        if self.bbox is None and self.region is None:
            raise ValueError("Provide either 'bbox' or 'region'")
        return self


class WindVector(BaseModel):
    """A single retrieved wind vector at a grid node."""

    lon: float
    lat: float
    speed: float = Field(..., description="10 m neutral wind speed [m/s]")
    direction: float = Field(
        ..., description="Meteorological direction wind blows FROM [deg, 0=N, CW]"
    )
    u: float = Field(..., description="Eastward wind component [m/s]")
    v: float = Field(..., description="Northward wind component [m/s]")


class WindFieldStats(BaseModel):
    n_vectors: int
    speed_min: float
    speed_max: float
    speed_mean: float
    direction_mean: float


class WindFieldResponse(BaseModel):
    """API response carrying the retrieved wind field."""

    date: DateType
    bbox: BoundingBox
    source: str
    grid_km: float
    crs: str = "EPSG:4326"
    stats: WindFieldStats
    vectors: list[WindVector]

    def to_geojson(self) -> dict:
        """Return the wind field as a GeoJSON FeatureCollection."""
        features = []
        for w in self.vectors:
            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [w.lon, w.lat]},
                    "properties": {
                        "speed": round(w.speed, 3),
                        "direction": round(w.direction, 2),
                        "u": round(w.u, 3),
                        "v": round(w.v, 3),
                    },
                }
            )
        return {
            "type": "FeatureCollection",
            "metadata": {
                "date": self.date.isoformat(),
                "source": self.source,
                "grid_km": self.grid_km,
                "units": {"speed": "m/s", "direction": "deg_from_north"},
            },
            "features": features,
        }
