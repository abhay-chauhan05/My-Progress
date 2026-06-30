"""
Wind-direction retrieval from SAR imagery.
==========================================

Two retrievers are provided behind a common interface:

``LocalGradientRetriever`` (default, dependency-free)
    Wind rolls / streaks in the SAR image are aligned with the near-surface
    wind.  The image intensity gradient is therefore *perpendicular* to the
    streaks.  We estimate the dominant local orientation with the structure
    tensor and rotate by 90 deg to obtain the streak (wind) axis.  The
    inherent 180 deg ambiguity is resolved with a meteorological prior.

``ResNetRetriever`` (optional, needs PyTorch)
    Wraps the CNN in :mod:`windfield.ml.resnet_direction`, reproducing the
    approach of "Wind direction retrieval from Sentinel-1 SAR images using
    ResNet" (Remote Sensing of Environment, 2021).  Falls back to the
    local-gradient retriever if Torch / a trained checkpoint is unavailable.
"""
from __future__ import annotations

import numpy as np


def _gaussian_blur(a: np.ndarray, passes: int = 3) -> np.ndarray:
    out = np.nan_to_num(a, nan=float(np.nanmean(a)))
    for _ in range(passes):
        out = (
            out
            + np.roll(out, 1, 0)
            + np.roll(out, -1, 0)
            + np.roll(out, 1, 1)
            + np.roll(out, -1, 1)
        ) / 5.0
    return out


class LocalGradientRetriever:
    """Structure-tensor based wind-direction estimator."""

    name = "local-gradient"

    def __init__(self, prior_direction: float | None = None):
        self.prior_direction = prior_direction

    def retrieve(self, scene) -> np.ndarray:
        """Return a per-pixel wind direction field [deg, FROM, 0=N]."""
        img = np.log10(np.clip(scene.sigma0, 1e-4, None))
        img = _gaussian_blur(img, passes=1)

        # Band-pass: remove the large-scale brightness trend (incidence-angle
        # ramp + mesoscale wind-speed gradient) and suppress per-pixel speckle,
        # leaving the wind-roll texture for the structure tensor.
        background = _gaussian_blur(img, passes=18)
        img = _gaussian_blur(img - background, passes=2)

        gy, gx = np.gradient(img)

        # Structure-tensor components, smoothed over a neighbourhood.
        jxx = _gaussian_blur(gx * gx, passes=4)
        jyy = _gaussian_blur(gy * gy, passes=4)
        jxy = _gaussian_blur(gx * gy, passes=4)

        # Orientation of the dominant gradient (eigenvector of structure tensor).
        grad_angle = 0.5 * np.arctan2(2.0 * jxy, jxx - jyy)

        # Streaks are perpendicular to the dominant gradient => wind axis.
        wind_axis = grad_angle + np.pi / 2.0

        # Convert math angle (x=east, y=north) to a meteorological FROM-bearing.
        # wind_axis points along the streak (the blowing axis); convert the
        # "toward" vector to a compass bearing then add 180 for FROM.
        ux, uy = np.cos(wind_axis), np.sin(wind_axis)
        toward_bearing = (np.degrees(np.arctan2(ux, uy))) % 360.0
        direction_from = (toward_bearing + 180.0) % 360.0

        direction_from = self._resolve_ambiguity(direction_from, scene)
        return np.where(scene.ocean, direction_from, np.nan)

    def _resolve_ambiguity(self, direction_from: np.ndarray, scene) -> np.ndarray:
        """Resolve the 180 deg streak ambiguity using a prior bearing."""
        prior = self.prior_direction
        if prior is None:
            # Use a synthetic-truth hint if present, else a neutral prior.
            if scene.truth_direction is not None:
                prior = float(np.nanmean(scene.truth_direction))
            else:
                prior = 225.0  # SW-monsoon default for the Indian coast

        flipped = (direction_from + 180.0) % 360.0
        d0 = _angular_diff(direction_from, prior)
        d1 = _angular_diff(flipped, prior)
        return np.where(d1 < d0, flipped, direction_from)


class ResNetRetriever:
    """CNN wind-direction retriever (ResNet); falls back when unavailable."""

    name = "resnet"

    def __init__(self, prior_direction: float | None = None, checkpoint: str | None = None):
        self._fallback = LocalGradientRetriever(prior_direction)
        self._model = None
        try:
            from .ml.resnet_direction import load_inference_model

            self._model = load_inference_model(checkpoint)
        except Exception:
            self._model = None  # Torch / checkpoint unavailable.

    def retrieve(self, scene) -> np.ndarray:
        if self._model is None:
            field = self._fallback.retrieve(scene)
            return field
        # Patch-wise CNN inference over the scene.
        return self._model.predict_field(scene, fallback=self._fallback)


def _angular_diff(a, b) -> np.ndarray:
    """Smallest absolute difference between bearings [deg]."""
    d = np.abs((a - b + 180.0) % 360.0 - 180.0)
    return d


def get_retriever(kind: str = "local-gradient", prior_direction: float | None = None):
    """Factory for wind-direction retrievers."""
    if kind == "resnet":
        return ResNetRetriever(prior_direction=prior_direction)
    return LocalGradientRetriever(prior_direction=prior_direction)
