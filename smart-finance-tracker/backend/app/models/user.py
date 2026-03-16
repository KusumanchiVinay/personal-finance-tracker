"""app/models/user.py"""
import uuid
from sqlalchemy import String, Boolean, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base
from app.models.mixins import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id:             Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email:          Mapped[str]       = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password:Mapped[str]       = mapped_column(Text, nullable=False)
    full_name:      Mapped[str]       = mapped_column(String(255), nullable=False)
    currency:       Mapped[str]       = mapped_column(String(10), default="USD")
    monthly_income: Mapped[float]     = mapped_column(Numeric(14, 2), default=0)
    is_active:      Mapped[bool]      = mapped_column(Boolean, default=True)
    is_verified:    Mapped[bool]      = mapped_column(Boolean, default=False)

    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    budgets      = relationship("Budget",      back_populates="user", cascade="all, delete-orphan")
