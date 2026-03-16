"""app/api/v1/endpoints/export.py — CSV import/export"""
import io
import csv
from datetime import date
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.transaction import Transaction

router = APIRouter()

EXPORT_HEADERS = ["date","type","amount","category","description","merchant","tags","note"]


@router.get("/csv")
async def export_csv(
    start_date: str = None, end_date: str = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    filters = [Transaction.user_id == user.id]
    if start_date: filters.append(Transaction.date >= start_date)
    if end_date:   filters.append(Transaction.date <= end_date)

    result = await db.execute(
        select(Transaction).where(*filters)
        .options(selectinload(Transaction.category))
        .order_by(Transaction.date.desc())
    )
    txs = result.scalars().all()

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=EXPORT_HEADERS)
    writer.writeheader()
    for tx in txs:
        writer.writerow({
            "date": str(tx.date),
            "type": tx.type,
            "amount": float(tx.amount),
            "category": tx.category.name if tx.category else "",
            "description": tx.description or "",
            "merchant": tx.merchant or "",
            "tags": ",".join(tx.tags or []),
            "note": tx.note or "",
        })
    output.seek(0)
    filename = f"transactions_{date.today()}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.post("/csv")
async def import_csv(
    file: UploadFile = File(...),
    db:   AsyncSession = Depends(get_db),
    user: User         = Depends(get_current_user),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Only CSV files accepted")

    content = await file.read()
    reader  = csv.DictReader(io.StringIO(content.decode("utf-8")))
    created, errors = 0, []

    for i, row in enumerate(reader, 1):
        try:
            tx = Transaction(
                user_id=user.id,
                amount=float(row.get("amount", 0)),
                type=row.get("type", "expense"),
                description=row.get("description"),
                merchant=row.get("merchant"),
                date=date.fromisoformat(row["date"]),
                tags=[t.strip() for t in (row.get("tags") or "").split(",") if t.strip()],
                note=row.get("note"),
            )
            db.add(tx)
            created += 1
        except Exception as e:
            errors.append({"row": i, "error": str(e)})

    return {"imported": created, "errors": errors}
