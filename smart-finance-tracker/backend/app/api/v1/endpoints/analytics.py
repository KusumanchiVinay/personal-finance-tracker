"""app/api/v1/endpoints/analytics.py — AI insights + dashboard"""
from datetime import date, datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.transaction import Transaction, Category
from app.services.ai_insights import AIInsightsService

router = APIRouter()


@router.get("/dashboard")
async def dashboard_summary(
    month: int = date.today().month,
    year:  int = date.today().year,
    db:    AsyncSession = Depends(get_db),
    user:  User = Depends(get_current_user),
):
    """Returns all data needed for the main dashboard."""
    # Monthly totals
    base = select(
        Transaction.type,
        func.sum(Transaction.amount).label("total")
    ).where(
        Transaction.user_id == user.id,
        extract("month", Transaction.date) == month,
        extract("year",  Transaction.date) == year,
    ).group_by(Transaction.type)

    result = await db.execute(base)
    totals: Dict[str, float] = {r.type: float(r.total) for r in result}

    income   = totals.get("income", 0)
    expenses = totals.get("expense", 0)
    savings  = income - expenses

    # Category breakdown (expenses)
    cat_q = await db.execute(
        select(Category.name, Category.icon, Category.color,
               func.sum(Transaction.amount).label("total"))
        .join(Transaction, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user.id,
            Transaction.type == "expense",
            extract("month", Transaction.date) == month,
            extract("year",  Transaction.date) == year,
        )
        .group_by(Category.name, Category.icon, Category.color)
        .order_by(func.sum(Transaction.amount).desc())
    )
    categories = [
        {"name": r.name, "icon": r.icon, "color": r.color, "amount": float(r.total)}
        for r in cat_q
    ]

    # 6-month trend
    trend_q = await db.execute(
        select(
            extract("year",  Transaction.date).label("y"),
            extract("month", Transaction.date).label("m"),
            Transaction.type,
            func.sum(Transaction.amount).label("total")
        )
        .where(Transaction.user_id == user.id)
        .group_by("y", "m", Transaction.type)
        .order_by("y", "m")
        .limit(12)
    )
    trend = {}
    for r in trend_q:
        key = f"{int(r.y)}-{int(r.m):02d}"
        if key not in trend:
            trend[key] = {"month": key, "income": 0, "expense": 0}
        trend[key][r.type] += float(r.total)

    # Recent anomalies
    anom_q = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user.id, Transaction.is_anomaly == True)
        .order_by(Transaction.date.desc())
        .limit(5)
    )
    anomalies = [
        {"id": str(tx.id), "amount": float(tx.amount),
         "description": tx.description, "date": str(tx.date)}
        for tx in anom_q.scalars()
    ]

    return {
        "month": month, "year": year,
        "income": income, "expenses": expenses,
        "savings": savings,
        "savings_rate": round(savings / income * 100, 1) if income > 0 else 0,
        "categories": categories,
        "monthly_trend": list(trend.values()),
        "anomalies": anomalies,
    }


@router.get("/insights")
async def get_ai_insights(
    db:   AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Full AI insights: health score, predictions, suggestions."""
    svc = AIInsightsService(db, user)
    return await svc.generate_all_insights()


@router.get("/health-score")
async def health_score(
    db:   AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = AIInsightsService(db, user)
    return await svc.compute_health_score()


@router.get("/prediction")
async def spending_prediction(
    db:   AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = AIInsightsService(db, user)
    return await svc.predict_next_month()
