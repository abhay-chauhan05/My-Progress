"""Geographic helpers: gridding, land masking and great-circle geometry."""
from __future__ import annotations

import math

import numpy as np

_EARTH_RADIUS_KM = 6371.0088


def km_to_deg_lat(km: float) -> float:
    """Convert a north-south distance in km to degrees of latitude."""
    return km / 111.32


def km_to_deg_lon(km: float, lat: float) -> float:
    """Convert an east-west distance in km to degrees of longitude at ``lat``."""
    return km / (111.32 * max(math.cos(math.radians(lat)), 1e-6))


def build_grid(
    bbox: tuple[float, float, float, float], grid_km: float
) -> tuple[np.ndarray, np.ndarray]:
    """Build a regular lon/lat grid covering ``bbox`` at ``grid_km`` spacing.

    Returns
    -------
    (lon2d, lat2d) : tuple of 2-D arrays
    """
    lon_min, lat_min, lon_max, lat_max = bbox
    lat_c = 0.5 * (lat_min + lat_max)

    dlat = km_to_deg_lat(grid_km)
    dlon = km_to_deg_lon(grid_km, lat_c)

    lats = np.arange(lat_min, lat_max + dlat * 0.5, dlat)
    lons = np.arange(lon_min, lon_max + dlon * 0.5, dlon)
    lon2d, lat2d = np.meshgrid(lons, lats)
    return lon2d, lat2d


def haversine_km(lon1, lat1, lon2, lat2) -> np.ndarray:
    """Great-circle distance in km between point arrays."""
    lon1, lat1, lon2, lat2 = map(np.radians, (lon1, lat1, lon2, lat2))
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * _EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))


def ocean_mask(lon2d: np.ndarray, lat2d: np.ndarray) -> np.ndarray:
    """Boolean mask, ``True`` over ocean.

    Uses the ``global-land-mask`` package when available (a packaged 1/4-deg
    land/sea grid); otherwise falls back to "everything is ocean".
    """
    try:
        from global_land_mask import globe

        return globe.is_ocean(lat2d, lon2d)
    except Exception:  # pragma: no cover - fallback path
        return np.ones(lon2d.shape, dtype=bool)


def speed_dir_to_uv(speed: np.ndarray, direction_from: np.ndarray):
    """Convert (speed, meteorological FROM-direction in deg) to (u, v).

    Meteorological convention: ``direction_from`` is the compass bearing the
    wind blows *from* (0 = from North, 90 = from East).  ``u`` is eastward,
    ``v`` is northward.
    """
    rad = np.radians(direction_from)
    u = -speed * np.sin(rad)
    v = -speed * np.cos(rad)
    return u, v


def uv_to_speed_dir(u: np.ndarray, v: np.ndarray):
    """Inverse of :func:`speed_dir_to_uv`."""
    speed = np.hypot(u, v)
    direction_from = (np.degrees(np.arctan2(-u, -v))) % 360.0
    return speed, direction_from
