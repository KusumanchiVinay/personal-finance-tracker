"""app/models/transaction.py"""
import uuid
from datetime import date
from typing import Optional, List
from sqlalchemy import String, Boolean, Numeric, Text, Date, ForeignKey, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base
from app.models.mixins import TimestampMixin


class Transaction(TimestampMixin, Base):
    __tablename__ = "transactions"

    id:           Mapped[uuid.UUID]     = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id:      Mapped[uuid.UUID]     = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    category_id:  Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id"))
    amount:       Mapped[float]         = mapped_column(Numeric(14, 2), nullable=False)
    type:         Mapped[str]           = mapped_column(String(20), nullable=False)  # income|expense
    description:  Mapped[Optional[str]] = mapped_column(Text)
    merchant:     Mapped[Optional[str]] = mapped_column(String(255))
    date:         Mapped[date]          = mapped_column(Date, nullable=False, index=True)
    is_recurring: Mapped[bool]          = mapped_column(Boolean, default=False)
    recur_period: Mapped[Optional[str]] = mapped_column(String(20))
    tags:         Mapped[List[str]]     = mapped_column(ARRAY(String), default=list)
    note:         Mapped[Optional[str]] = mapped_column(Text)
    is_anomaly:   Mapped[bool]          = mapped_column(Boolean, default=False)
    anomaly_score:Mapped[Optional[float]] = mapped_column(Numeric(5, 4))

    user     = relationship("User",     back_populates="transactions")
    category = relationship("Category", back_populates="transactions")


class Category(Base):
    __tablename__ = "categories"

    id:         Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id:    Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    name:       Mapped[str]  = mapped_column(String(100), nullable=False)
    icon:       Mapped[str]  = mapped_column(String(50), default="💰")
    color:      Mapped[str]  = mapped_column(String(7), default="#6366f1")
    type:       Mapped[str]  = mapped_column(String(20), default="expense")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    transactions = relationship("Transaction", back_populates="category")


class Budget(Base):
    __tablename__ = "budgets"

    id:          Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id:     Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)
    amount:      Mapped[float]     = mapped_column(Numeric(14, 2), nullable=False)
    period:      Mapped[str]       = mapped_column(String(20), default="monthly")
    month:       Mapped[Optional[int]] = mapped_column()
    year:        Mapped[Optional[int]] = mapped_column()
    alert_at:    Mapped[float]     = mapped_column(Numeric(5, 2), default=80.0)

    user     = relationship("User",     back_populates="budgets")
    category = relationship("Category")
