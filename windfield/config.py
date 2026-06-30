"""Application configuration loaded from environment / ``.env``."""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the wind-field service."""

    model_config = SettingsConfigDict(
        env_prefix="WINDFIELD_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Data source selection: "auto" | "synthetic" | "copernicus"
    source: str = "auto"

    # Default spacing of returned wind vectors (km).
    grid_km: float = 2.0

    # Storage directory for cached / downloaded products.
    data_dir: Path = Path("data")

    # Copernicus Data Space Ecosystem credentials (optional).
    cdse_username: str | None = None
    cdse_password: str | None = None

    # Study-area presets (lon_min, lat_min, lon_max, lat_max).
    # Tamil Nadu coast (Gulf of Mannar / Palk Strait region).
    tamilnadu_bbox: tuple[float, float, float, float] = (78.0, 8.0, 80.5, 11.0)
    # Gujarat coast (Gulf of Khambhat / Kutch region).
    gujarat_bbox: tuple[float, float, float, float] = (68.0, 20.0, 72.5, 23.5)

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"

    def has_copernicus_credentials(self) -> bool:
        return bool(self.cdse_username and self.cdse_password)


settings = Settings()
