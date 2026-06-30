"""
FastAPI service for ocean wind-field estimation.
================================================

Endpoints
---------
GET  /                         -> redirect to the interactive map viewer
GET  /health                   -> liveness probe
GET  /regions                  -> available study-area presets
POST /windfield                -> wind field (JSON) for a date + AOI
GET  /windfield                -> same, via query params (convenient for links)
GET  /windfield.geojson        -> wind field as a GeoJSON FeatureCollection
GET  /windfield.png            -> rendered quiver map (like the sample figure)
GET  /docs                     -> OpenAPI / Swagger UI (provided by FastAPI)
"""
from __future__ import annotations

from datetime import date as date_type
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from .. import __version__
from ..config import settings
from ..estimator import WindFieldEstimator, resolve_bbox
from ..schemas import BoundingBox, WindFieldRequest, WindFieldResponse

app = FastAPI(
    title="Ocean Wind-Field Estimation API",
    description=(
        "Estimate 10 m ocean wind-field vectors from Sentinel-1 SAR imagery "
        "over Indian coastal areas (Tamil Nadu / Gujarat) for offshore "
        "wind-farm planning. Wind speed is retrieved by inverting the CMOD5.N "
        "geophysical model function; wind direction from SAR streak analysis "
        "(local-gradient / ResNet)."
    ),
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
if _FRONTEND_DIR.exists():
    app.mount("/viewer", StaticFiles(directory=str(_FRONTEND_DIR), html=True), name="viewer")


def _estimate(req: WindFieldRequest) -> WindFieldResponse:
    bbox = resolve_bbox(req.region, req.bbox)
    estimator = WindFieldEstimator(source=req.source)
    try:
        return estimator.estimate(req.date, bbox, grid_km=req.grid_km)
    except Exception as exc:  # pragma: no cover - surfaced to the client
        raise HTTPException(status_code=500, detail=f"Estimation failed: {exc}") from exc


@app.get("/", include_in_schema=False)
def root():
    if _FRONTEND_DIR.exists():
        return RedirectResponse(url="/viewer/")
    return {"service": "windfield", "version": __version__, "docs": "/docs"}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": __version__,
        "default_source": settings.source,
        "copernicus_configured": settings.has_copernicus_credentials(),
    }


@app.get("/regions")
def regions():
    return {
        "tamilnadu": {
            "bbox": settings.tamilnadu_bbox,
            "description": "Tamil Nadu coast (Gulf of Mannar / Palk Strait)",
        },
        "gujarat": {
            "bbox": settings.gujarat_bbox,
            "description": "Gujarat coast (Gulf of Khambhat / Kutch)",
        },
    }


@app.post("/windfield", response_model=WindFieldResponse)
def windfield_post(req: WindFieldRequest):
    return _estimate(req)


def _request_from_query(
    date: date_type,
    region: str | None,
    lon_min: float | None,
    lat_min: float | None,
    lon_max: float | None,
    lat_max: float | None,
    grid_km: float | None,
    source: str | None,
) -> WindFieldRequest:
    bbox = None
    if None not in (lon_min, lat_min, lon_max, lat_max):
        bbox = BoundingBox(
            lon_min=lon_min, lat_min=lat_min, lon_max=lon_max, lat_max=lat_max
        )
    try:
        return WindFieldRequest(
            date=date, region=region, bbox=bbox, grid_km=grid_km, source=source
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/windfield", response_model=WindFieldResponse)
def windfield_get(
    date: date_type = Query(..., description="Acquisition date YYYY-MM-DD"),
    region: str | None = Query(None, description="tamilnadu | gujarat"),
    lon_min: float | None = Query(None),
    lat_min: float | None = Query(None),
    lon_max: float | None = Query(None),
    lat_max: float | None = Query(None),
    grid_km: float | None = Query(None, gt=0.2, le=25),
    source: str | None = Query(None),
):
    req = _request_from_query(
        date, region, lon_min, lat_min, lon_max, lat_max, grid_km, source
    )
    return _estimate(req)


@app.get("/windfield.geojson")
def windfield_geojson(
    date: date_type = Query(...),
    region: str | None = Query(None),
    lon_min: float | None = Query(None),
    lat_min: float | None = Query(None),
    lon_max: float | None = Query(None),
    lat_max: float | None = Query(None),
    grid_km: float | None = Query(None, gt=0.2, le=25),
    source: str | None = Query(None),
):
    req = _request_from_query(
        date, region, lon_min, lat_min, lon_max, lat_max, grid_km, source
    )
    return _estimate(req).to_geojson()


@app.get("/windfield.png")
def windfield_png(
    date: date_type = Query(...),
    region: str | None = Query(None),
    lon_min: float | None = Query(None),
    lat_min: float | None = Query(None),
    lon_max: float | None = Query(None),
    lat_max: float | None = Query(None),
    grid_km: float | None = Query(None, gt=0.2, le=25),
    source: str | None = Query(None),
):
    from ..visualize import render_quiver_png

    req = _request_from_query(
        date, region, lon_min, lat_min, lon_max, lat_max, grid_km, source
    )
    result = _estimate(req)
    png_bytes = render_quiver_png(result)
    return Response(content=png_bytes, media_type="image/png")
