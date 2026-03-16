"""app/schemas/transaction.py"""
from datetime import date
from typing import Optional, List
from pydantic import BaseModel, field_validator
import uuid


class TransactionCreate(BaseModel):
    amount:       float
    type:         str        # income | expense
    category_id:  Optional[uuid.UUID] = None
    description:  Optional[str] = None
    merchant:     Optional[str] = None
    date:         date
    is_recurring: bool = False
    recur_period: Optional[str] = None
    tags:         List[str] = []
    note:         Optional[str] = None

    @field_validator("amount")
    @classmethod
    def positive_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be positive")
        return round(v, 2)

    @field_validator("type")
    @classmethod
    def valid_type(cls, v: str) -> str:
        if v not in ("income", "expense"):
            raise ValueError("type must be 'income' or 'expense'")
        return v


class TransactionUpdate(BaseModel):
    amount:       Optional[float] = None
    type:         Optional[str]   = None
    category_id:  Optional[uuid.UUID] = None
    description:  Optional[str]   = None
    merchant:     Optional[str]   = None
    date:         Optional[date]  = None
    is_recurring: Optional[bool]  = None
    recur_period: Optional[str]   = None
    tags:         Optional[List[str]] = None
    note:         Optional[str]   = None


class TransactionOut(BaseModel):
    id:           uuid.UUID
    amount:       float
    type:         str
    category_id:  Optional[uuid.UUID]
    category_name:Optional[str] = None
    category_icon:Optional[str] = None
    description:  Optional[str]
    merchant:     Optional[str]
    date:         date
    is_recurring: bool
    tags:         List[str]
    note:         Optional[str]
    is_anomaly:   bool
    anomaly_score:Optional[float]
    created_at:   str

    class Config:
        from_attributes = True


class TransactionFilter(BaseModel):
    start_date:  Optional[date]   = None
    end_date:    Optional[date]   = None
    type:        Optional[str]    = None
    category_id: Optional[uuid.UUID] = None
    min_amount:  Optional[float]  = None
    max_amount:  Optional[float]  = None
    search:      Optional[str]    = None
    page:        int = 1
    per_page:    int = 20


class PaginatedTransactions(BaseModel):
    items:    List[TransactionOut]
    total:    int
    page:     int
    per_page: int
    pages:    int
