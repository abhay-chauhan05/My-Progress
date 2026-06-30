"""API tests using FastAPI's TestClient."""
from fastapi.testclient import TestClient

from windfield.api.app import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_regions():
    r = client.get("/regions")
    assert r.status_code == 200
    assert "tamilnadu" in r.json()


def test_windfield_post():
    r = client.post(
        "/windfield",
        json={"date": "2024-01-15", "region": "tamilnadu", "grid_km": 8.0},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["stats"]["n_vectors"] > 0
    assert body["source"].startswith("synthetic")
    assert len(body["vectors"]) == body["stats"]["n_vectors"]


def test_windfield_get_with_bbox():
    r = client.get(
        "/windfield",
        params={
            "date": "2024-06-20",
            "lon_min": 68.0, "lat_min": 20.0,
            "lon_max": 70.0, "lat_max": 22.0,
            "grid_km": 8.0,
        },
    )
    assert r.status_code == 200
    assert r.json()["stats"]["n_vectors"] >= 0


def test_windfield_geojson():
    r = client.get(
        "/windfield.geojson",
        params={"date": "2024-01-15", "region": "gujarat", "grid_km": 8.0},
    )
    assert r.status_code == 200
    assert r.json()["type"] == "FeatureCollection"


def test_windfield_png():
    r = client.get(
        "/windfield.png",
        params={"date": "2024-01-15", "region": "tamilnadu", "grid_km": 10.0},
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_missing_area_is_rejected():
    r = client.post("/windfield", json={"date": "2024-01-15"})
    assert r.status_code == 422
