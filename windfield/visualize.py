"""Render a wind-field quiver map (arrows coloured by wind speed)."""
from __future__ import annotations

import io

import numpy as np

from .schemas import WindFieldResponse


def render_quiver_png(result: WindFieldResponse, dpi: int = 110) -> bytes:
    """Render the wind field as a PNG quiver plot resembling the sample figure.

    Arrows show wind direction; colour encodes wind speed [m/s].
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if not result.vectors:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, "No ocean wind vectors in AOI", ha="center", va="center")
        ax.axis("off")
        return _fig_to_png(fig, dpi)

    lon = np.array([w.lon for w in result.vectors])
    lat = np.array([w.lat for w in result.vectors])
    u = np.array([w.u for w in result.vectors])
    v = np.array([w.v for w in result.vectors])
    speed = np.array([w.speed for w in result.vectors])

    fig, ax = plt.subplots(figsize=(9, 7))
    q = ax.quiver(
        lon,
        lat,
        u,
        v,
        speed,
        cmap="jet",
        scale=350,
        width=0.0025,
        clim=(max(0, speed.min()), speed.max()),
    )
    cbar = fig.colorbar(q, ax=ax, orientation="horizontal", pad=0.08, shrink=0.85)
    cbar.set_label("wind speed (m/s)")

    ax.set_xlabel("Longitude (deg E)")
    ax.set_ylabel("Latitude (deg N)")
    ax.set_title(
        f"Sentinel-1 ocean wind field  |  {result.date.isoformat()}\n"
        f"source: {result.source}  |  mean speed: {result.stats.speed_mean:.1f} m/s"
    )
    ax.set_xlim(result.bbox.lon_min, result.bbox.lon_max)
    ax.set_ylim(result.bbox.lat_min, result.bbox.lat_max)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, linestyle=":", alpha=0.4)

    return _fig_to_png(fig, dpi)


def save_quiver_png(result: WindFieldResponse, path: str, dpi: int = 110) -> str:
    data = render_quiver_png(result, dpi=dpi)
    with open(path, "wb") as fh:
        fh.write(data)
    return path


def _fig_to_png(fig, dpi: int) -> bytes:
    import matplotlib.pyplot as plt

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()
