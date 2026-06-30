"""
windfield
=========

Ocean wind-field estimation from Sentinel-1 SAR imagery over Indian coastal
areas (Tamil Nadu / Gujarat) for offshore wind-farm planning.

The package exposes:

* :mod:`windfield.cmod5n`        - CMOD5.N geophysical model function (GMF).
* :mod:`windfield.wind_direction`- wind-direction retrieval (local-gradient + ResNet).
* :mod:`windfield.sar_source`    - Sentinel-1 acquisition (Copernicus + synthetic).
* :mod:`windfield.estimator`     - end-to-end wind-field estimator.
* :mod:`windfield.api.app`       - FastAPI application.
"""

__version__ = "1.0.0"

from .schemas import (  # noqa: F401
    BoundingBox,
    WindFieldRequest,
    WindVector,
    WindFieldResponse,
)
