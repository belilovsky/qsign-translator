from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
import tempfile


@dataclass(frozen=True)
class Settings:
    environment: str
    database_url: str | None
    asset_root: str
    generated_media_root: str
    model_cache: str
    review_token: str | None


def get_settings() -> Settings:
    return Settings(
        environment=os.environ.get("QSIGN_ENV", "local"),
        database_url=os.environ.get("DATABASE_URL"),
        asset_root=os.environ.get("QSIGN_ASSET_ROOT", "/assets"),
        generated_media_root=os.environ.get(
            "QSIGN_GENERATED_MEDIA_ROOT",
            str(Path(tempfile.gettempdir()) / "qsign-generated-media"),
        ),
        model_cache=os.environ.get("QSIGN_MODEL_CACHE", "/models"),
        review_token=os.environ.get("QSIGN_REVIEW_TOKEN"),
    )
