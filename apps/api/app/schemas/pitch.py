"""Pitch DTO for read responses (detail view)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.pitch import PitchStatus


class PitchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    status: PitchStatus
    text: str | None = None
    model: str | None = None
    grounding_ok: bool = False
    created_at: datetime | None = None


class PitchGenerateRequest(BaseModel):
    force: bool = False  # bypass cache and regenerate


# --- Bulk generation (spec §4.7) ---

BULK_MAX_CUSTOMERS = 200


class BulkPitchRequest(BaseModel):
    customer_ids: list[str] = Field(min_length=1, max_length=BULK_MAX_CUSTOMERS)
    force: bool = False


class BulkBatchCreated(BaseModel):
    batch_id: int
    total: int


class BulkItemStatus(BaseModel):
    customer_id: str
    status: Literal["pending", "running", "succeeded", "failed"]
    pitch_id: int | None = None
    error: str | None = None


class BulkBatchStatus(BaseModel):
    batch_id: int
    total: int
    completed: int  # terminal items (succeeded + failed)
    succeeded: int
    failed: int
    running: int
    pending: int
    complete: bool  # whole batch finished
    live: bool  # True from the in-memory registry; False when reconstructed from the DB
    items: list[BulkItemStatus]
