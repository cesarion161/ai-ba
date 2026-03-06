"""UI configuration endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.ui_config import UIConfig

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("/ui", response_model=UIConfig)
async def get_ui_config() -> UIConfig:
    return UIConfig()
