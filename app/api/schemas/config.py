"""Response schemas for UI configuration."""

from __future__ import annotations

from app.core.ui_config import UIConfig as UIConfigSchema

# Re-export the UIConfig directly as the response schema
UIConfigResponse = UIConfigSchema
