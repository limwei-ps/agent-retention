"""Pitch ORM model (spec §1.4). Generation logic lands in Day 3; the table exists now so the
customer detail can return the latest pitch (null until generated)."""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.customer import Customer


class PitchStatus(str, enum.Enum):
    not_generated = "not_generated"
    generating = "generating"
    ready = "ready"
    failed = "failed"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Pitch(Base):
    __tablename__ = "pitches"
    # Composite indexes matching the two cache-lookup access paths (equality columns first, then the
    # ORDER BY column) so lookups stay O(log n) as the append-only table grows.
    __table_args__ = (
        Index("ix_pitch_cache_lookup", "customer_id", "cache_key", "created_at"),
        Index("ix_pitch_customer_created", "customer_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True)

    status: Mapped[PitchStatus] = mapped_column(
        Enum(PitchStatus, native_enum=False), default=PitchStatus.not_generated
    )
    text: Mapped[str | None] = mapped_column(Text, default=None)
    cache_key: Mapped[str | None] = mapped_column(String, index=True, default=None)

    model: Mapped[str | None] = mapped_column(String, default=None)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    grounding_ok: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    customer: Mapped["Customer"] = relationship(back_populates="pitches")
