"""
End-to-end ocean wind-field estimator.
======================================

Pipeline
--------
1. Acquire a calibrated Sentinel-1 VV sigma0 scene for the AOI/date
   (:mod:`windfield.sar_source`).
2. Retrieve the wind *direction* field (:mod:`windfield.wind_direction`).
3. Compute ``phi`` = (wind direction - radar look direction) and invert the
   CMOD5.N GMF to obtain the 10 m neutral wind *speed*.
4. Mask land, decompose into (u, v) components and subsample to the requested
   output grid spacing.
"""
from __future__ import annotations

from datetime import date as date_type

import numpy as np

from . import geo
from .cmod5n import cmod5n_inverse
from .config import settings
from .sar_source import get_source
from .schemas import (
    BoundingBox,
    WindFieldResponse,
    WindFieldStats,
    WindVector,
)
from .wind_direction import get_retriever


def resolve_bbox(region: str | None, bbox: BoundingBox | None) -> BoundingBox:
    """Resolve a named region preset or pass through an explicit bbox."""
    if bbox is not None:
        return bbox
    presets = {
        "tamilnadu": settings.tamilnadu_bbox,
        "gujarat": settings.gujarat_bbox,
    }
    if region not in presets:
        raise ValueError(f"Unknown region '{region}'")
    lon_min, lat_min, lon_max, lat_max = presets[region]
    return BoundingBox(
        lon_min=lon_min, lat_min=lat_min, lon_max=lon_max, lat_max=lat_max
    )


class WindFieldEstimator:
    """Coordinates SAR acquisition, direction retrieval and CMOD5.N inversion."""

    def __init__(self, source: str | None = None, direction_method: str = "local-gradient"):
        self.source_name = source or settings.source
        self.direction_method = direction_method

    def estimate(
        self,
        d: date_type,
        bbox: BoundingBox,
        grid_km: float | None = None,
    ) -> WindFieldResponse:
        grid_km = grid_km or settings.grid_km
        source = get_source(self.source_name)
        scene = source.get_scene(bbox.as_tuple(), d, grid_km)

        retriever = get_retriever(self.direction_method)
        direction = retriever.retrieve(scene)

        # phi = wind direction relative to radar azimuth look direction.
        phi = direction - scene.look_direction
        speed = cmod5n_inverse(scene.sigma0, phi, scene.incidence, iterations=12)

        # Apply ocean mask.
        ocean = scene.ocean & np.isfinite(scene.sigma0)
        speed = np.where(ocean, speed, np.nan)
        direction = np.where(ocean, direction, np.nan)

        u, v = geo.speed_dir_to_uv(speed, direction)

        vectors = self._collect_vectors(scene.lon2d, scene.lat2d, speed, direction, u, v)
        stats = self._stats(vectors)

        return WindFieldResponse(
            date=d,
            bbox=bbox,
            source=scene.source,
            grid_km=grid_km,
            stats=stats,
            vectors=vectors,
        )

    @staticmethod
    def _collect_vectors(lon2d, lat2d, speed, direction, u, v) -> list[WindVector]:
        vectors: list[WindVector] = []
        valid = np.isfinite(speed) & np.isfinite(direction)
        idx = np.argwhere(valid)
        for j, i in idx:
            vectors.append(
                WindVector(
                    lon=float(lon2d[j, i]),
                    lat=float(lat2d[j, i]),
                    speed=float(speed[j, i]),
                    direction=float(direction[j, i]),
                    u=float(u[j, i]),
                    v=float(v[j, i]),
                )
            )
        return vectors

    @staticmethod
    def _stats(vectors: list[WindVector]) -> WindFieldStats:
        if not vectors:
            return WindFieldStats(
                n_vectors=0,
                speed_min=0.0,
                speed_max=0.0,
                speed_mean=0.0,
                direction_mean=0.0,
            )
        speeds = np.array([w.speed for w in vectors])
        # Vector-mean direction (avoids the 0/360 wrap problem).
        us = np.array([w.u for w in vectors])
        vs = np.array([w.v for w in vectors])
        mean_dir = float((np.degrees(np.arctan2(-us.mean(), -vs.mean()))) % 360.0)
        return WindFieldStats(
            n_vectors=len(vectors),
            speed_min=float(speeds.min()),
            speed_max=float(speeds.max()),
            speed_mean=float(speeds.mean()),
            direction_mean=mean_dir,
        )
