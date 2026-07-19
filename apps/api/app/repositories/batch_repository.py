"""Batch data-access behind an interface, injected via FastAPI `Depends()` (spec §4.7)."""

from __future__ import annotations

from typing import Protocol

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.batch import PitchBatch


class BatchRepository(Protocol):
    def create(self, customer_ids: list[str], total: int) -> PitchBatch: ...
    def get(self, batch_id: int) -> PitchBatch | None: ...


class SqlBatchRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, customer_ids: list[str], total: int) -> PitchBatch:
        batch = PitchBatch(customer_ids=customer_ids, total=total)
        self._db.add(batch)
        self._db.commit()  # short transaction — mitigates SQLite write-lock contention (spec §4.5)
        self._db.refresh(batch)
        return batch

    def get(self, batch_id: int) -> PitchBatch | None:
        return self._db.get(PitchBatch, batch_id)


def get_batch_repository(db: Session = Depends(get_db)) -> SqlBatchRepository:
    return SqlBatchRepository(db)
