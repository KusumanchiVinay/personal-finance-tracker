"""
app/models/ — SQLAlchemy ORM models (mirrors the SQL schema)
"""
import uuid
from datetime import date, datetime, timezone
from sqlalchemy import (
    Boolean, Column, Date, ForeignKey, Integer,
    Numeric, SmallInteger, String, Text, ARRAY,
    UniqueConstraint, CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMPTZ
from sqlalchemy.orm import relationship
from app.db.session import Base


def _uuid():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc)


# ─────────────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email           = Column(String(255), unique=True, nullable=False, index=True)
    username        = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(Text, nullable=False)
    full_name       = Column(String(255))
    currency        = Column(String(10), default="USD")
    monthly_income  = Column(Numeric(12, 2), default=0)
    avatar_url      = Column(Text)
    is_active       = Column(Boolean, default=True)
    is_verified     = Column(Boolean, default=False)
    created_at      = Column(TIMESTAMPTZ, default=_now)
    updated_at      = Column(TIMESTAMPTZ, default=_now, onupdate=_now)

    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    budgets      = relationship("Budget",      back_populates="user", cascade="all, delete-orphan")
    categories   = relationship("Category",    back_populates="user", cascade="all, delete-orphan")
    snapshots    = relationship("AnalyticsSnapshot", back_populates="user", cascade="all, delete-orphan")


# ─────────────────────────────────────────────────────────────────────────────
class Category(Base):
    __tablename__ = "categories"

    id        = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id   = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    name      = Column(String(100), nullable=False)
    icon      = Column(String(50), default="💰")
    color     = Column(String(20), default="#6366f1")
    type      = Column(String(20), default="expense")
    is_system = Column(Boolean, default=False)
    created_at = Column(TIMESTAMPTZ, default=_now)

    user         = relationship("User", back_populates="categories")
    transactions = relationship("Transaction", back_populates="category")
    budgets      = relationship("Budget", back_populates="category")


# ─────────────────────────────────────────────────────────────────────────────
class Transaction(Base):
    __tablename__ = "transactions"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id         = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id     = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    title           = Column(String(255), nullable=False)
    description     = Column(Text)
    amount          = Column(Numeric(12, 2), nullable=False)
    type            = Column(String(20), nullable=False)   # 'expense' | 'income'
    date            = Column(Date, nullable=False, index=True)
    tags            = Column(ARRAY(Text), default=[])
    receipt_url     = Column(Text)
    is_recurring    = Column(Boolean, default=False)
    recurrence_rule = Column(String(50))
    source          = Column(String(50), default="manual")
    created_at      = Column(TIMESTAMPTZ, default=_now)
    updated_at      = Column(TIMESTAMPTZ, default=_now, onupdate=_now)

    user     = relationship("User",     back_populates="transactions")
    category = relationship("Category", back_populates="transactions")


# ─────────────────────────────────────────────────────────────────────────────
class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (UniqueConstraint("user_id", "category_id", "month", "year"),)

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id      = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id  = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="CASCADE"))
    month        = Column(SmallInteger, nullable=False)
    year         = Column(SmallInteger, nullable=False)
    amount       = Column(Numeric(12, 2), nullable=False)
    alert_at_pct = Column(SmallInteger, default=80)
    created_at   = Column(TIMESTAMPTZ, default=_now)
    updated_at   = Column(TIMESTAMPTZ, default=_now, onupdate=_now)

    user     = relationship("User",     back_populates="budgets")
    category = relationship("Category", back_populates="budgets")


# ─────────────────────────────────────────────────────────────────────────────
class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"
    __table_args__ = (UniqueConstraint("user_id", "year", "month"),)

    id                     = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id                = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    month                  = Column(SmallInteger, nullable=False)
    year                   = Column(SmallInteger, nullable=False)
    total_income           = Column(Numeric(12, 2), default=0)
    total_expense          = Column(Numeric(12, 2), default=0)
    net_savings            = Column(Numeric(12, 2), default=0)
    savings_rate           = Column(Numeric(5, 2),  default=0)
    financial_health_score = Column(SmallInteger, default=0)
    category_breakdown     = Column(JSONB)
    top_categories         = Column(JSONB)
    anomalies              = Column(JSONB)
    predicted_next_month   = Column(Numeric(12, 2))
    ml_insights            = Column(JSONB)
    computed_at            = Column(TIMESTAMPTZ, default=_now)

    user = relationship("User", back_populates="snapshots")
