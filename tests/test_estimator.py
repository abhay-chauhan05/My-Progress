"""Tests for the end-to-end estimator and validation harness."""
from datetime import date

import numpy as np

from windfield.estimator import WindFieldEstimator, resolve_bbox
from windfield.geo import speed_dir_to_uv, uv_to_speed_dir
from windfield.schemas import BoundingBox
from windfield.validation import validate_case


def test_uv_roundtrip():
    speed = np.array([5.0, 10.0])
    direction = np.array([45.0, 230.0])
    u, v = speed_dir_to_uv(speed, direction)
    s2, d2 = uv_to_speed_dir(u, v)
    assert np.allclose(s2, speed, atol=1e-6)
    assert np.allclose(d2, direction, atol=1e-6)


def test_estimator_produces_ocean_vectors():
    est = WindFieldEstimator(source="synthetic")
    bbox = resolve_bbox("tamilnadu", None)
    result = est.estimate(date(2024, 1, 15), bbox, grid_km=6.0)
    assert result.stats.n_vectors > 0
    assert 0.0 < result.stats.speed_mean < 40.0
    # All returned vectors should carry finite components.
    for w in result.vectors[:50]:
        assert np.isfinite(w.u) and np.isfinite(w.v)
        assert 0.0 <= w.direction <= 360.0


def test_geojson_structure():
    est = WindFieldEstimator(source="synthetic")
    bbox = BoundingBox(lon_min=78.0, lat_min=8.0, lon_max=80.0, lat_max=10.0)
    result = est.estimate(date(2024, 6, 20), bbox, grid_km=8.0)
    gj = result.to_geojson()
    assert gj["type"] == "FeatureCollection"
    assert "metadata" in gj
    if gj["features"]:
        f = gj["features"][0]
        assert f["geometry"]["type"] == "Point"
        assert "speed" in f["properties"]


def test_validation_speed_skill():
    # Synthetic round-trip: CMOD5.N inversion with the true direction should
    # recover wind speed with small RMSE and high correlation.
    r = validate_case((78.0, 8.0, 80.5, 11.0), date(2024, 1, 15), grid_km=4.0)
    assert r.n_points > 50
    assert r.speed_rmse < 1.0
    assert r.speed_corr > 0.95
