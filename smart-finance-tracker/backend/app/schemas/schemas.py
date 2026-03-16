"""
app/schemas/ — Pydantic v2 request/response models
"""
from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Any
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, model_validator


# ─── Auth ─────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    email:          EmailStr
    username:       str = Field(min_length=3, max_length=50)
    password:       str = Field(min_length=8)
    full_name:      Optional[str] = None
    monthly_income: Optional[Decimal] = Field(default=0, ge=0)
    currency:       str = Field(default="USD", max_length=10)


class UserLogin(BaseModel):
    email:    EmailStr
    password: str


class UserOut(BaseModel):
    id:             UUID
    email:          str
    username:       str
    full_name:      Optional[str]
    currency:       str
    monthly_income: Decimal
    avatar_url:     Optional[str]
    is_active:      bool
    created_at:     datetime

    model_config = {"from_attributes": True}


class TokenPair(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    user:          UserOut


class TokenRefresh(BaseModel):
    refresh_token: str


# ─── Categories ───────────────────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    name:  str = Field(min_length=1, max_length=100)
    icon:  str = Field(default="💰")
    color: str = Field(default="#6366f1")
    type:  str = Field(default="expense")


class CategoryOut(BaseModel):
    id:        UUID
    name:      str
    icon:      str
    color:     str
    type:      str
    is_system: bool

    model_config = {"from_attributes": True}


# ─── Transactions ─────────────────────────────────────────────────────────────

class TransactionCreate(BaseModel):
    title:           str = Field(min_length=1, max_length=255)
    description:     Optional[str] = None
    amount:          Decimal = Field(gt=0)
    type:            str     = Field(pattern="^(expense|income)$")
    category_id:     Optional[UUID] = None
    date:            date
    tags:            List[str] = []
    is_recurring:    bool = False
    recurrence_rule: Optional[str] = None


class TransactionUpdate(BaseModel):
    title:       Optional[str]    = None
    description: Optional[str]    = None
    amount:      Optional[Decimal] = Field(default=None, gt=0)
    type:        Optional[str]    = None
    category_id: Optional[UUID]   = None
    date:        Optional[date]   = None
    tags:        Optional[List[str]] = None


class TransactionOut(BaseModel):
    id:              UUID
    title:           str
    description:     Optional[str]
    amount:          Decimal
    type:            str
    date:            date
    tags:            List[str]
    is_recurring:    bool
    recurrence_rule: Optional[str]
    source:          str
    created_at:      datetime
    category:        Optional[CategoryOut]

    model_config = {"from_attributes": True}


class TransactionPage(BaseModel):
    items:   List[TransactionOut]
    total:   int
    page:    int
    size:    int
    pages:   int


# ─── Budgets ──────────────────────────────────────────────────────────────────

class BudgetCreate(BaseModel):
    category_id:  UUID
    month:        int = Field(ge=1, le=12)
    year:         int = Field(ge=2020, le=2100)
    amount:       Decimal = Field(gt=0)
    alert_at_pct: int = Field(default=80, ge=1, le=100)


class BudgetOut(BaseModel):
    id:           UUID
    month:        int
    year:         int
    amount:       Decimal
    alert_at_pct: int
    spent:        Decimal = 0   # computed field — injected by service
    remaining:    Decimal = 0
    pct_used:     float   = 0
    category:     Optional[CategoryOut]

    model_config = {"from_attributes": True}


# ─── Analytics / AI ───────────────────────────────────────────────────────────

class CategoryBreakdownItem(BaseModel):
    category_id:   Optional[str]
    category_name: str
    icon:          str
    color:         str
    amount:        Decimal
    pct:           float
    tx_count:      int


class MonthlyTrend(BaseModel):
    year:    int
    month:   int
    income:  Decimal
    expense: Decimal
    savings: Decimal


class AnomalyItem(BaseModel):
    transaction_id: UUID
    title:          str
    amount:         Decimal
    date:           date
    reason:         str
    severity:       str   # 'low' | 'medium' | 'high'
    z_score:        Optional[float] = None


class AIInsight(BaseModel):
    type:        str   # 'tip' | 'warning' | 'achievement' | 'prediction'
    title:       str
    description: str
    impact:      Optional[str] = None   # 'positive' | 'negative' | 'neutral'
    value:       Optional[Any] = None


class AnalyticsDashboard(BaseModel):
    month:                  int
    year:                   int
    total_income:           Decimal
    total_expense:          Decimal
    net_savings:            Decimal
    savings_rate:           float
    financial_health_score: int
    category_breakdown:     List[CategoryBreakdownItem]
    monthly_trend:          List[MonthlyTrend]
    anomalies:              List[AnomalyItem]
    predicted_next_month:   Optional[Decimal]
    ai_insights:            List[AIInsight]
    budget_status:          List[BudgetOut]
