"""Customer ORM model (spec §1.2)."""

from __future__ import annotations

from datetime import date

from sqlalchemy import JSON, Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # e.g. "CUST-00042"
    name: Mapped[str] = mapped_column(String, index=True)
    email: Mapped[str] = mapped_column(String)
    phone: Mapped[str] = mapped_column(String)

    current_plan_id: Mapped[str] = mapped_column(String, index=True)
    monthly_price: Mapped[int] = mapped_column(Integer)  # RM; may sit below list (legacy promo)
    tenure_months: Mapped[int] = mapped_column(Integer)
    contract_end_date: Mapped[date] = mapped_column(Date, index=True)
    region: Mapped[str] = mapped_column(String)

    # Usage: full 12-month history as a JSON value object (always loaded with the customer),
    # plus derived scalars promoted to columns for sort/filter.
    usage_archetype: Mapped[str] = mapped_column(String)  # flat_low | climbing | heavy
    usage_history: Mapped[list[dict]] = mapped_column(JSON, default=list)
    avg_monthly_gb: Mapped[int] = mapped_column(Integer, index=True)
    last_month_gb: Mapped[int] = mapped_column(Integer)

    pitches: Mapped[list["Pitch"]] = relationship(  # noqa: F821
        back_populates="customer",
        cascade="all, delete-orphan",
        order_by="Pitch.created_at.desc()",
    )
