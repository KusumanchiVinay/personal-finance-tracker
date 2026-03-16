"""
app/services/transaction_service.py — CRUD + CSV import/export
"""
import csv
import io
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.models.models import Transaction, Category
from app.schemas.schemas import TransactionCreate, TransactionUpdate


# ─── helpers ──────────────────────────────────────────────────────────────────

async def _get_or_raise(db: AsyncSession, tx_id: UUID, user_id: UUID) -> Transaction:
    result = await db.execute(
        select(Transaction)
        .options(selectinload(Transaction.category))
        .where(Transaction.id == tx_id, Transaction.user_id == user_id)
    )
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx


# ─── CRUD ─────────────────────────────────────────────────────────────────────

async def create_transaction(db: AsyncSession, data: TransactionCreate, user_id: UUID) -> Transaction:
    tx = Transaction(user_id=user_id, source="manual", **data.model_dump())
    db.add(tx)
    await db.flush()
    await db.refresh(tx)
    result = await db.execute(
        select(Transaction).options(selectinload(Transaction.category)).where(Transaction.id == tx.id)
    )
    return result.scalar_one()


async def list_transactions(
    db: AsyncSession,
    user_id: UUID,
    page: int = 1,
    size: int = 20,
    type_filter: Optional[str] = None,
    category_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
) -> tuple[list[Transaction], int]:
    q = (
        select(Transaction)
        .options(selectinload(Transaction.category))
        .where(Transaction.user_id == user_id)
    )
    if type_filter:
        q = q.where(Transaction.type == type_filter)
    if category_id:
        q = q.where(Transaction.category_id == category_id)
    if start_date:
        q = q.where(Transaction.date >= start_date)
    if end_date:
        q = q.where(Transaction.date <= end_date)
    if search:
        q = q.where(Transaction.title.ilike(f"%{search}%"))

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar_one()

    q = q.order_by(desc(Transaction.date), desc(Transaction.created_at))
    q = q.offset((page - 1) * size).limit(size)
    items = (await db.execute(q)).scalars().all()
    return list(items), total


async def get_transaction(db: AsyncSession, tx_id: UUID, user_id: UUID) -> Transaction:
    return await _get_or_raise(db, tx_id, user_id)


async def update_transaction(db: AsyncSession, tx_id: UUID, user_id: UUID, data: TransactionUpdate) -> Transaction:
    tx = await _get_or_raise(db, tx_id, user_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(tx, field, value)
    await db.flush()
    await db.refresh(tx)
    return tx


async def delete_transaction(db: AsyncSession, tx_id: UUID, user_id: UUID) -> None:
    tx = await _get_or_raise(db, tx_id, user_id)
    await db.delete(tx)
    await db.flush()


# ─── CSV Export ───────────────────────────────────────────────────────────────

async def export_csv(db: AsyncSession, user_id: UUID) -> str:
    result = await db.execute(
        select(Transaction)
        .options(selectinload(Transaction.category))
        .where(Transaction.user_id == user_id)
        .order_by(desc(Transaction.date))
    )
    transactions = result.scalars().all()

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["date", "title", "description", "type", "category", "amount", "tags", "is_recurring"],
    )
    writer.writeheader()
    for tx in transactions:
        writer.writerow({
            "date":         str(tx.date),
            "title":        tx.title,
            "description":  tx.description or "",
            "type":         tx.type,
            "category":     tx.category.name if tx.category else "",
            "amount":       str(tx.amount),
            "tags":         ",".join(tx.tags or []),
            "is_recurring": str(tx.is_recurring),
        })
    return output.getvalue()


# ─── CSV Import ───────────────────────────────────────────────────────────────

async def import_csv(db: AsyncSession, user_id: UUID, content: bytes) -> dict:
    """
    Expected columns: date,title,amount,type,category (optional: description,tags)
    Returns counts of imported and failed rows.
    """
    # Build category name→id lookup
    cat_result = await db.execute(
        select(Category).where(
            (Category.user_id == user_id) | (Category.is_system == True)  # noqa
        )
    )
    cat_map = {c.name.lower(): c.id for c in cat_result.scalars().all()}

    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    imported, failed = 0, 0
    errors = []

    for i, row in enumerate(reader, start=2):
        try:
            cat_name = (row.get("category") or "Other").lower()
            cat_id = cat_map.get(cat_name)

            tx = Transaction(
                user_id=user_id,
                title=row["title"].strip(),
                description=row.get("description", "").strip() or None,
                amount=Decimal(row["amount"]),
                type=row["type"].lower().strip(),
                category_id=cat_id,
                date=datetime.strptime(row["date"].strip(), "%Y-%m-%d").date(),
                tags=[t.strip() for t in (row.get("tags") or "").split(",") if t.strip()],
                source="csv",
            )
            db.add(tx)
            imported += 1
        except Exception as e:
            failed += 1
            errors.append(f"Row {i}: {e}")

    await db.flush()
    return {"imported": imported, "failed": failed, "errors": errors[:10]}
