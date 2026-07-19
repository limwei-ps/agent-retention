"""Plan reference DTO."""

from __future__ import annotations

from pydantic import BaseModel


class PlanRef(BaseModel):
    id: str
    name: str
    speed_mbps: int
    price_myr: int
