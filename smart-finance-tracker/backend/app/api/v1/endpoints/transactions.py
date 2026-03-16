"""app/api/v1/endpoints/transactions.py — full CRUD + filters"""
import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.transaction import Transaction, Category
from app.schemas.transaction import (
    TransactionCreate, TransactionUpdate, TransactionOut,
    PaginatedTransactions
)

router = APIRouter()


def _tx_to_out(tx: Transaction) -> TransactionOut:
    return TransactionOut(
        id=tx.id,
        amount=float(tx.amount),
        type=tx.type,
        category_id=tx.category_id,
        category_name=tx.category.name  if tx.category else None,
        category_icon=tx.category.icon  if tx.category else None,
        description=tx.description,
        merchant=tx.merchant,
        date=tx.date,
        is_recurring=tx.is_recurring,
        tags=tx.tags or [],
        note=tx.note,
        is_anomaly=tx.is_anomaly,
        anomaly_score=float(tx.anomaly_score) if tx.anomaly_score else None,
        created_at=tx.created_at.isoformat(),
    )


@router.get("", response_model=PaginatedTransactions)
async def list_transactions(
    page:        int   = Query(1, ge=1),
    per_page:    int   = Query(20, ge=1, le=100),
    type:        Optional[str] = None,
    category_id: Optional[str] = None,
    start_date:  Optional[str] = None,
    end_date:    Optional[str] = None,
    search:      Optional[str] = None,
    db:          AsyncSession  = Depends(get_db),
    user:        User          = Depends(get_current_user),
):
    filters = [Transaction.user_id == user.id]
    if type:        filters.append(Transaction.type == type)
    if category_id: filters.append(Transaction.category_id == category_id)
    if start_date:  filters.append(Transaction.date >= start_date)
    if end_date:    filters.append(Transaction.date <= end_date)
    if search:
        term = f"%{search}%"
        filters.append(
            (Transaction.description.ilike(term)) |
            (Transaction.merchant.ilike(term))
        )

    count_q = await db.execute(select(func.count()).where(and_(*filters)).select_from(Transaction))
    total = count_q.scalar() or 0

    q = (
        select(Transaction)
        .where(and_(*filters))
        .options(selectinload(Transaction.category))
        .order_by(Transaction.date.desc(), Transaction.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(q)
    items = [_tx_to_out(tx) for tx in result.scalars().all()]

    return PaginatedTransactions(
        items=items, total=total, page=page,
        per_page=per_page, pages=math.ceil(total / per_page)
    )


@router.post("", response_model=TransactionOut, status_code=201)
async def create_transaction(
    payload: TransactionCreate,
    db:      AsyncSession = Depends(get_db),
    user:    User         = Depends(get_current_user),
):
    tx = Transaction(**payload.model_dump(), user_id=user.id)
    db.add(tx)
    await db.flush()
    await db.refresh(tx, ["category"])
    return _tx_to_out(tx)


@router.get("/{tx_id}", response_model=TransactionOut)
async def get_transaction(
    tx_id: str,
    db:    AsyncSession = Depends(get_db),
    user:  User         = Depends(get_current_user),
):
    result = await db.execute(
        select(Transaction)
        .where(Transaction.id == tx_id, Transaction.user_id == user.id)
        .options(selectinload(Transaction.category))
    )
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(404, "Transaction not found")
    return _tx_to_out(tx)


@router.patch("/{tx_id}", response_model=TransactionOut)
async def update_transaction(
    tx_id:   str,
    payload: TransactionUpdate,
    db:      AsyncSession = Depends(get_db),
    user:    User         = Depends(get_current_user),
):
    result = await db.execute(
        select(Transaction)
        .where(Transaction.id == tx_id, Transaction.user_id == user.id)
        .options(selectinload(Transaction.category))
    )
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(404, "Transaction not found")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(tx, k, v)
    await db.flush()
    await db.refresh(tx, ["category"])
    return _tx_to_out(tx)


@router.delete("/{tx_id}", status_code=204)
async def delete_transaction(
    tx_id: str,
    db:    AsyncSession = Depends(get_db),
    user:  User         = Depends(get_current_user),
):
    result = await db.execute(
        select(Transaction).where(Transaction.id == tx_id, Transaction.user_id == user.id)
    )
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(404, "Transaction not found")
    await db.delete(tx)
