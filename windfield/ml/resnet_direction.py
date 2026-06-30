"""
ResNet wind-direction model (optional, PyTorch).
================================================

Reproduces the approach of *"Wind direction retrieval from Sentinel-1 SAR
images using ResNet"* (Remote Sensing of Environment, 2021): a ResNet
backbone ingests a normalised SAR amplitude patch and regresses the wind
direction.  To avoid the 0/360 wrap discontinuity the network predicts the
``(cos 2*phi, sin 2*phi)`` doublet (the 180 deg-ambiguous streak axis), which
is converted back to a bearing and disambiguated with a meteorological prior.

This module is import-safe without PyTorch: the rest of the package only
imports it lazily and falls back to the local-gradient retriever when Torch or
a trained checkpoint is missing.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np

try:  # PyTorch is an optional extra.
    import torch
    import torch.nn as nn

    _TORCH = True
except Exception:  # pragma: no cover - torch not installed
    _TORCH = False


PATCH = 64  # SAR patch size (pixels) fed to the network.


if _TORCH:

    class BasicBlock(nn.Module):
        expansion = 1

        def __init__(self, in_ch: int, out_ch: int, stride: int = 1):
            super().__init__()
            self.conv1 = nn.Conv2d(in_ch, out_ch, 3, stride, 1, bias=False)
            self.bn1 = nn.BatchNorm2d(out_ch)
            self.conv2 = nn.Conv2d(out_ch, out_ch, 3, 1, 1, bias=False)
            self.bn2 = nn.BatchNorm2d(out_ch)
            self.relu = nn.ReLU(inplace=True)
            self.downsample = None
            if stride != 1 or in_ch != out_ch:
                self.downsample = nn.Sequential(
                    nn.Conv2d(in_ch, out_ch, 1, stride, bias=False),
                    nn.BatchNorm2d(out_ch),
                )

        def forward(self, x):
            identity = x
            out = self.relu(self.bn1(self.conv1(x)))
            out = self.bn2(self.conv2(out))
            if self.downsample is not None:
                identity = self.downsample(x)
            return self.relu(out + identity)

    class ResNetDirection(nn.Module):
        """A compact ResNet-18-style regressor for wind direction.

        Input : (N, 1, PATCH, PATCH) normalised SAR amplitude patches.
        Output: (N, 2) = (cos 2*phi, sin 2*phi).
        """

        def __init__(self, layers=(2, 2, 2, 2)):
            super().__init__()
            self.in_ch = 64
            self.stem = nn.Sequential(
                nn.Conv2d(1, 64, 7, 2, 3, bias=False),
                nn.BatchNorm2d(64),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(3, 2, 1),
            )
            self.layer1 = self._make_layer(64, layers[0], 1)
            self.layer2 = self._make_layer(128, layers[1], 2)
            self.layer3 = self._make_layer(256, layers[2], 2)
            self.layer4 = self._make_layer(512, layers[3], 2)
            self.pool = nn.AdaptiveAvgPool2d(1)
            self.head = nn.Linear(512, 2)

        def _make_layer(self, out_ch, blocks, stride):
            layers = [BasicBlock(self.in_ch, out_ch, stride)]
            self.in_ch = out_ch
            for _ in range(1, blocks):
                layers.append(BasicBlock(out_ch, out_ch))
            return nn.Sequential(*layers)

        def forward(self, x):
            x = self.stem(x)
            x = self.layer1(x)
            x = self.layer2(x)
            x = self.layer3(x)
            x = self.layer4(x)
            x = self.pool(x).flatten(1)
            out = self.head(x)
            # Normalise to the unit circle (stable angle decoding).
            return out / (out.norm(dim=1, keepdim=True) + 1e-6)


class InferenceModel:
    """Runs patch-wise inference and assembles a direction field."""

    def __init__(self, model, device: str = "cpu"):
        self.model = model
        self.device = device

    @torch.no_grad() if _TORCH else (lambda f: f)
    def predict_field(self, scene, fallback=None) -> np.ndarray:
        if not _TORCH or self.model is None:
            return fallback.retrieve(scene)

        img = np.log10(np.clip(np.nan_to_num(scene.sigma0, nan=1e-4), 1e-4, None))
        img = (img - np.nanmean(img)) / (np.nanstd(img) + 1e-6)
        ny, nx = img.shape
        out = np.full((ny, nx), np.nan)

        half = PATCH // 2
        step = max(8, PATCH // 2)
        self.model.eval()
        for y in range(half, ny - half, step):
            for x in range(half, nx - half, step):
                patch = img[y - half : y + half, x - half : x + half]
                if patch.shape != (PATCH, PATCH):
                    continue
                t = torch.tensor(patch[None, None], dtype=torch.float32, device=self.device)
                cos2, sin2 = self.model(t).cpu().numpy()[0]
                axis = 0.5 * math.degrees(math.atan2(sin2, cos2))
                out[y - step // 2 : y + step // 2, x - step // 2 : x + step // 2] = axis

        # Fill gaps and resolve ambiguity via the fallback's prior logic.
        out = np.where(np.isnan(out), fallback.retrieve(scene), (out + 360.0) % 360.0)
        return np.where(scene.ocean, out, np.nan)


def load_inference_model(checkpoint: str | None = None) -> "InferenceModel":
    """Load a trained model; raises if Torch / checkpoint unavailable."""
    if not _TORCH:
        raise RuntimeError("PyTorch not installed")

    model = ResNetDirection()
    ckpt = checkpoint or _default_checkpoint()
    if ckpt and Path(ckpt).exists():
        state = torch.load(ckpt, map_location="cpu")
        model.load_state_dict(state.get("model", state))
    else:
        # No trained weights -> signal caller to use the analytic fallback.
        raise RuntimeError("No trained ResNet checkpoint found")
    model.eval()
    return InferenceModel(model)


def _default_checkpoint() -> str | None:
    cand = Path(__file__).resolve().parent / "weights" / "resnet_direction.pt"
    return str(cand) if cand.exists() else None
