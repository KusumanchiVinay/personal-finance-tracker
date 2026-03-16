"""app/api/v1/endpoints/budgets.py"""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from sqlalchemy.orm import selectinload
from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.transaction import Budget, Transaction, Category
from app.schemas.budget import BudgetCreate, BudgetOut
import uuid

router = APIRouter()


@router.get("")
async def list_budgets(
    month: int = date.today().month,
    year:  int = date.today().year,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Budget)
        .where(Budget.user_id == user.id, Budget.month == month, Budget.year == year)
        .options(selectinload(Budget.category))
    )
    budgets = result.scalars().all()

    out = []
    for b in budgets:
        spent_q = await db.execute(
            select(func.sum(Transaction.amount)).where(
                Transaction.user_id == user.id,
                Transaction.category_id == b.category_id,
                Transaction.type == "expense",
                extract("month", Transaction.date) == month,
                extract("year",  Transaction.date) == year,
            )
        )
        spent = float(spent_q.scalar() or 0)
        out.append(BudgetOut(
            id=b.id, category_id=b.category_id,
            category_name=b.category.name if b.category else None,
            category_icon=b.category.icon if b.category else None,
            amount=float(b.amount), period=b.period,
            month=b.month, year=b.year, alert_at=float(b.alert_at),
            spent=spent, pct_used=round(spent / float(b.amount) * 100, 1) if b.amount else 0
        ))
    return out


@router.post("", response_model=BudgetOut, status_code=201)
async def create_budget(payload: BudgetCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    b = Budget(**payload.model_dump(), user_id=user.id)
    db.add(b)
    await db.flush()
    await db.refresh(b, ["category"])
    return BudgetOut(id=b.id, category_id=b.category_id,
                     category_name=b.category.name if b.category else None,
                     category_icon=b.category.icon if b.category else None,
                     amount=float(b.amount), period=b.period,
                     month=b.month, year=b.year, alert_at=float(b.alert_at))


@router.delete("/{budget_id}", status_code=204)
async def delete_budget(budget_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Budget).where(Budget.id == budget_id, Budget.user_id == user.id))
    b = result.scalar_one_or_none()
    if not b:
        raise HTTPException(404, "Budget not found")
    await db.delete(b)
