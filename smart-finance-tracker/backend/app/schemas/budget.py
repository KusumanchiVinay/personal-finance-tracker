"""app/schemas/budget.py"""
from typing import Optional
from pydantic import BaseModel
import uuid


class BudgetCreate(BaseModel):
    category_id: uuid.UUID
    amount:      float
    period:      str = "monthly"
    month:       Optional[int] = None
    year:        Optional[int] = None
    alert_at:    float = 80.0


class BudgetOut(BaseModel):
    id:           uuid.UUID
    category_id:  uuid.UUID
    category_name:Optional[str] = None
    category_icon:Optional[str] = None
    amount:       float
    period:       str
    month:        Optional[int]
    year:         Optional[int]
    alert_at:     float
    spent:        float = 0
    pct_used:     float = 0

    class Config:
        from_attributes = True
