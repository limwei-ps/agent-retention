"""Shared DTOs: the paginated list envelope."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    data: list[T]
    page: int
    page_size: int
    total: int
