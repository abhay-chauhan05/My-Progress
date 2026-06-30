"""Command-line interface for offline wind-field retrieval.

Examples
--------
    python -m windfield.cli --region tamilnadu --date 2024-01-15 --png out.png
    python -m windfield.cli --bbox 78 8 80.5 11 --date 2024-06-20 --geojson wf.json
"""
from __future__ import annotations

import argparse
import json
from datetime import date

from .estimator import WindFieldEstimator, resolve_bbox
from .schemas import BoundingBox


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Sentinel-1 ocean wind-field retrieval")
    p.add_argument("--date", required=True, help="YYYY-MM-DD")
    p.add_argument("--region", choices=["tamilnadu", "gujarat"])
    p.add_argument(
        "--bbox", nargs=4, type=float, metavar=("LON_MIN", "LAT_MIN", "LON_MAX", "LAT_MAX")
    )
    p.add_argument("--grid-km", type=float, default=4.0)
    p.add_argument("--source", default="auto")
    p.add_argument("--png", help="write a quiver map to this path")
    p.add_argument("--geojson", help="write GeoJSON to this path")
    args = p.parse_args(argv)

    bbox = None
    if args.bbox:
        bbox = BoundingBox(
            lon_min=args.bbox[0], lat_min=args.bbox[1],
            lon_max=args.bbox[2], lat_max=args.bbox[3],
        )
    bbox = resolve_bbox(args.region, bbox)

    est = WindFieldEstimator(source=args.source)
    result = est.estimate(date.fromisoformat(args.date), bbox, grid_km=args.grid_km)

    s = result.stats
    print(f"Date        : {result.date}")
    print(f"Source      : {result.source}")
    print(f"BBox        : {bbox.as_tuple()}")
    print(f"Vectors     : {s.n_vectors}")
    print(f"Wind speed  : min {s.speed_min:.2f} | mean {s.speed_mean:.2f} | "
          f"max {s.speed_max:.2f} m/s")
    print(f"Mean dir    : {s.direction_mean:.1f} deg (from)")

    if args.geojson:
        with open(args.geojson, "w") as fh:
            json.dump(result.to_geojson(), fh)
        print(f"GeoJSON     -> {args.geojson}")

    if args.png:
        from .visualize import save_quiver_png

        save_quiver_png(result, args.png)
        print(f"Quiver map  -> {args.png}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
