"""
Validation harness.
===================

Because the synthetic source stores the ground-truth wind field used to
generate the SAR backscatter, we can quantify the retrieval skill end-to-end:

* generate truth wind -> CMOD5.N forward -> speckle -> sigma0
* run the full retrieval (direction + CMOD5.N inverse)
* compare retrieved vs truth: speed bias / RMSE / correlation, direction RMSE.

This mirrors the "validation results table" deliverable.  Against real data the
same statistics would be computed versus ERA5 / scatterometer / buoy winds.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date as date_type

import numpy as np

from .cmod5n import cmod5n_inverse
from .sar_source import SyntheticSARSource
from .wind_direction import _angular_diff, get_retriever


@dataclass
class ValidationResult:
    date: str
    bbox: tuple
    n_points: int
    speed_bias: float
    speed_rmse: float
    speed_corr: float
    direction_rmse: float
    direction_within_30deg_pct: float

    def as_dict(self) -> dict:
        return asdict(self)


def validate_case(
    bbox: tuple[float, float, float, float],
    d: date_type,
    grid_km: float = 3.0,
    direction_method: str = "local-gradient",
) -> ValidationResult:
    """Run a single synthetic round-trip validation case."""
    scene = SyntheticSARSource().get_scene(bbox, d, grid_km)
    ocean = scene.ocean & np.isfinite(scene.sigma0)

    # --- Speed: invert CMOD5.N using the TRUE direction (isolates the GMF) ---
    phi_true = scene.truth_direction - scene.look_direction
    speed_ret = cmod5n_inverse(scene.sigma0, phi_true, scene.incidence, iterations=14)

    truth_s = scene.truth_speed[ocean]
    ret_s = speed_ret[ocean]
    valid = np.isfinite(truth_s) & np.isfinite(ret_s)
    truth_s, ret_s = truth_s[valid], ret_s[valid]

    bias = float(np.mean(ret_s - truth_s))
    rmse = float(np.sqrt(np.mean((ret_s - truth_s) ** 2)))
    corr = float(np.corrcoef(ret_s, truth_s)[0, 1]) if len(truth_s) > 2 else float("nan")

    # --- Direction: evaluate the retriever vs truth ---
    retriever = get_retriever(direction_method)
    dir_ret = retriever.retrieve(scene)
    truth_d = scene.truth_direction[ocean]
    rd = dir_ret[ocean]
    dvalid = np.isfinite(truth_d) & np.isfinite(rd)
    diff = _angular_diff(rd[dvalid], truth_d[dvalid])
    dir_rmse = float(np.sqrt(np.mean(diff ** 2))) if diff.size else float("nan")
    within30 = float(100.0 * np.mean(diff <= 30.0)) if diff.size else float("nan")

    return ValidationResult(
        date=d.isoformat(),
        bbox=tuple(round(b, 3) for b in bbox),
        n_points=int(valid.sum()),
        speed_bias=round(bias, 3),
        speed_rmse=round(rmse, 3),
        speed_corr=round(corr, 4),
        direction_rmse=round(dir_rmse, 2),
        direction_within_30deg_pct=round(within30, 1),
    )


def run_validation_suite(grid_km: float = 3.0) -> list[ValidationResult]:
    """Validate across both study regions and several monsoon-phase dates."""
    from .config import settings

    cases = [
        (settings.tamilnadu_bbox, date_type(2024, 1, 15)),   # NE monsoon
        (settings.tamilnadu_bbox, date_type(2024, 7, 10)),   # SW monsoon
        (settings.gujarat_bbox, date_type(2024, 2, 20)),     # NE monsoon
        (settings.gujarat_bbox, date_type(2024, 6, 25)),     # SW monsoon
    ]
    return [validate_case(bbox, d, grid_km=grid_km) for bbox, d in cases]


def format_table(results: list[ValidationResult]) -> str:
    """Render results as a Markdown table."""
    header = (
        "| Region/Date | N | Speed bias (m/s) | Speed RMSE (m/s) | "
        "Speed corr | Dir RMSE (deg) | Dir <30 deg (%) |\n"
        "|---|---:|---:|---:|---:|---:|---:|\n"
    )
    rows = []
    for r in results:
        rows.append(
            f"| {r.bbox} {r.date} | {r.n_points} | {r.speed_bias:+.2f} | "
            f"{r.speed_rmse:.2f} | {r.speed_corr:.3f} | {r.direction_rmse:.1f} | "
            f"{r.direction_within_30deg_pct:.1f} |"
        )
    return header + "\n".join(rows)


if __name__ == "__main__":
    res = run_validation_suite()
    print(format_table(res))
