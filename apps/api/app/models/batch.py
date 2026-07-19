"""Bulk-pitch batch ORM model (spec §4.7).

A batch records *which* customers a bulk run targeted and *how many*, so a poll/stream for a batch the
in-memory registry no longer holds (e.g. after a process restart) can be reconstructed best-effort
from the DB — see `BatchRegistry` and the bulk routes. Per-item progress lives in the registry, not
here; we deliberately do NOT stamp a `batch_id` onto `Pitch` (cache hits reuse older rows, which would
make such a column unreliable for progress). See docs/take-home-plan.md §8.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PitchBatch(Base):
    __tablename__ = "pitch_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    total: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
