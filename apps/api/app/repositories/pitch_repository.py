"""Pitch data-access. The `pitches` table doubles as the cache (append-only: a new row per
generation, keyed by cache_key) — see spec §4.3."""

from __future__ import annotations

from typing import Protocol

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.pitch import Pitch, PitchStatus


class PitchRepository(Protocol):
    def get_ready_by_cache_key(self, customer_id: str, cache_key: str) -> Pitch | None: ...
    def get_latest_ready_for_customer(self, customer_id: str) -> Pitch | None: ...
    def create(self, **fields) -> Pitch: ...


class SqlPitchRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_ready_by_cache_key(self, customer_id: str, cache_key: str) -> Pitch | None:
        stmt = (
            select(Pitch)
            .where(
                Pitch.customer_id == customer_id,
                Pitch.cache_key == cache_key,
                Pitch.status == PitchStatus.ready,
            )
            .order_by(Pitch.created_at.desc(), Pitch.id.desc())  # id tiebreaks equal timestamps
            .limit(1)
        )
        return self._db.scalars(stmt).first()

    def get_latest_ready_for_customer(self, customer_id: str) -> Pitch | None:
        stmt = (
            select(Pitch)
            .where(Pitch.customer_id == customer_id, Pitch.status == PitchStatus.ready)
            .order_by(Pitch.created_at.desc(), Pitch.id.desc())
            .limit(1)
        )
        return self._db.scalars(stmt).first()

    def create(self, **fields) -> Pitch:
        pitch = Pitch(**fields)
        self._db.add(pitch)
        self._db.commit()  # short transaction — mitigates SQLite write-lock contention (spec §4.5)
        self._db.refresh(pitch)
        return pitch


def get_pitch_repository(db: Session = Depends(get_db)) -> SqlPitchRepository:
    return SqlPitchRepository(db)
