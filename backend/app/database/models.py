from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class CitizenModel(Base):
    __tablename__ = "citizens"

    citizen_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    cases: Mapped[list["CaseModel"]] = relationship(back_populates="citizen")


class CaseModel(Base):
    __tablename__ = "cases"

    case_id: Mapped[str] = mapped_column(String(20), primary_key=True)

    citizen_id: Mapped[str] = mapped_column(
        ForeignKey("citizens.citizen_id"),
        nullable=False,
    )

    program: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)

    opened_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime)

    citizen: Mapped["CitizenModel"] = relationship(back_populates="cases")
    payments: Mapped[list["PaymentModel"]] = relationship(back_populates="case")


class PaymentModel(Base):
    __tablename__ = "payments"

    payment_id: Mapped[str] = mapped_column(String(30), primary_key=True)

    case_id: Mapped[str] = mapped_column(
        ForeignKey("cases.case_id"),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    paid_date: Mapped[date | None] = mapped_column(Date)

    status: Mapped[str] = mapped_column(String(30), nullable=False)

    case: Mapped["CaseModel"] = relationship(back_populates="payments")