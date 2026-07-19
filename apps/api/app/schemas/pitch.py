"""Pitch DTO for read responses (detail view)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.pitch import PitchStatus


class PitchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    status: PitchStatus
    text: str | None = None
    model: str | None = None
    grounding_ok: bool = False
    created_at: datetime | None = None
