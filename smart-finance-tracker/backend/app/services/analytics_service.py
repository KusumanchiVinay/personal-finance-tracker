"""
app/services/analytics_service.py
────────────────────────────────────────────────────────────
Full analytics pipeline:
  • Monthly summary (income / expense / savings)
  • Category breakdown
  • Monthly trend (last 12 months)
  • Financial health score (0–100)
  • Spending prediction (linear regression via scikit-learn)
  • Anomaly detection (z-score per category)
  • AI-generated text insights
"""
from __future__ import annotations

import math
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

import numpy as np
from sqlalchemy import select, func, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import Transaction, Budget, Category, User
from app.schemas.schemas import (
    AnalyticsDashboard, CategoryBreakdownItem, MonthlyTrend,
    AnomalyItem, AIInsight, BudgetOut, CategoryOut,
)


# ─── helpers ──────────────────────────────────────────────────────────────────

async def _fetch_transactions(
    db: AsyncSession,
    user_id: UUID,
    start: date,
    end: date,
) -> list[Transaction]:
    result = await db.execute(
        select(Transaction)
        .options(selectinload(Transaction.category))
        .where(
            Transaction.user_id == user_id,
            Transaction.date >= start,
            Transaction.date <= end,
        )
    )
    return list(result.scalars().all())


async def _fetch_all_expense_history(db: AsyncSession, user_id: UUID) -> list[Transaction]:
    """Fetch up to 24 months of expense transactions for ML."""
    cutoff = date.today().replace(day=1) - timedelta(days=730)
    result = await db.execute(
        select(Transaction)
        .where(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.date >= cutoff,
        )
        .order_by(Transaction.date)
    )
    return list(result.scalars().all())


# ─── Category breakdown ───────────────────────────────────────────────────────

def _build_category_breakdown(transactions: list[Transaction]) -> list[CategoryBreakdownItem]:
    totals: dict[str, dict] = {}
    total_expense = sum(float(t.amount) for t in transactions if t.type == "expense")

    for tx in transactions:
        if tx.type != "expense":
            continue
        key = str(tx.category_id) if tx.category_id else "uncategorized"
        if key not in totals:
            totals[key] = {
                "category_id":   key,
                "category_name": tx.category.name if tx.category else "Uncategorized",
                "icon":          tx.category.icon  if tx.category else "📦",
                "color":         tx.category.color if tx.category else "#94a3b8",
                "amount":        0.0,
                "tx_count":      0,
            }
        totals[key]["amount"]   += float(tx.amount)
        totals[key]["tx_count"] += 1

    breakdown = []
    for item in sorted(totals.values(), key=lambda x: x["amount"], reverse=True):
        pct = (item["amount"] / total_expense * 100) if total_expense > 0 else 0
        breakdown.append(CategoryBreakdownItem(
            category_id=item["category_id"],
            category_name=item["category_name"],
            icon=item["icon"],
            color=item["color"],
            amount=Decimal(str(round(item["amount"], 2))),
            pct=round(pct, 1),
            tx_count=item["tx_count"],
        ))
    return breakdown


# ─── Monthly trend ────────────────────────────────────────────────────────────

async def _build_monthly_trend(db: AsyncSession, user_id: UUID, months: int = 12) -> list[MonthlyTrend]:
    today = date.today()
    trends = []
    for i in range(months - 1, -1, -1):
        # walk backwards month by month
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        start = date(y, m, 1)
        next_m = m + 1 if m < 12 else 1
        next_y = y if m < 12 else y + 1
        end = date(next_y, next_m, 1) - timedelta(days=1)

        txs = await _fetch_transactions(db, user_id, start, end)
        income  = sum(float(t.amount) for t in txs if t.type == "income")
        expense = sum(float(t.amount) for t in txs if t.type == "expense")
        trends.append(MonthlyTrend(
            year=y, month=m,
            income=Decimal(str(round(income, 2))),
            expense=Decimal(str(round(expense, 2))),
            savings=Decimal(str(round(income - expense, 2))),
        ))
    return trends


# ─── Financial health score ───────────────────────────────────────────────────

def _health_score(
    income: float,
    expense: float,
    savings_rate: float,
    over_budget_cats: int,
    anomaly_count: int,
) -> int:
    """
    Composite 0-100 score from multiple weighted signals:
    - Savings rate        (0–40 pts)
    - Expense ratio       (0–30 pts)
    - Budget adherence    (0–20 pts)
    - Anomaly penalty     (0–10 pts deducted)
    """
    # Savings rate component (40 pts max)
    savings_pts = min(40, savings_rate * 2)   # 20% savings → 40 pts

    # Expense ratio (30 pts max)
    if income > 0:
        ratio = expense / income
        expense_pts = max(0, 30 * (1 - ratio))
    else:
        expense_pts = 0

    # Budget adherence (20 pts max)
    budget_pts = max(0, 20 - over_budget_cats * 5)

    # Anomaly penalty (up to -10)
    anomaly_penalty = min(10, anomaly_count * 3)

    raw = savings_pts + expense_pts + budget_pts - anomaly_penalty
    return max(0, min(100, round(raw)))


# ─── Spending prediction (linear regression) ─────────────────────────────────

def _predict_next_month(history: list[Transaction]) -> Optional[float]:
    """
    Predict next month's total expense using linear regression
    over the per-month aggregates of the last N months.
    """
    try:
        from sklearn.linear_model import LinearRegression

        monthly: dict[str, float] = {}
        for tx in history:
            key = f"{tx.date.year}-{tx.date.month:02d}"
            monthly[key] = monthly.get(key, 0.0) + float(tx.amount)

        if len(monthly) < 3:
            return None

        sorted_months = sorted(monthly.items())
        X = np.array(range(len(sorted_months))).reshape(-1, 1)
        y = np.array([v for _, v in sorted_months])

        model = LinearRegression()
        model.fit(X, y)
        next_idx = len(sorted_months)
        prediction = float(model.predict([[next_idx]])[0])
        return max(0, round(prediction, 2))
    except Exception:
        return None


# ─── Anomaly detection (z-score) ─────────────────────────────────────────────

def _detect_anomalies(transactions: list[Transaction]) -> list[AnomalyItem]:
    """
    Within each category bucket, flag transactions that are
    > 2 standard deviations above the mean as anomalies.
    """
    from collections import defaultdict

    buckets: dict[str, list[Transaction]] = defaultdict(list)
    for tx in transactions:
        if tx.type == "expense":
            key = str(tx.category_id) if tx.category_id else "other"
            buckets[key].append(tx)

    anomalies: list[AnomalyItem] = []
    for cat_key, txs in buckets.items():
        if len(txs) < 3:
            continue
        amounts = np.array([float(t.amount) for t in txs])
        mean, std = amounts.mean(), amounts.std()
        if std == 0:
            continue
        for tx in txs:
            z = (float(tx.amount) - mean) / std
            if z > 2.0:
                severity = "high" if z > 3.0 else "medium" if z > 2.5 else "low"
                anomalies.append(AnomalyItem(
                    transaction_id=tx.id,
                    title=tx.title,
                    amount=tx.amount,
                    date=tx.date,
                    reason=f"Amount is {z:.1f}× standard deviations above category average",
                    severity=severity,
                    z_score=round(z, 2),
                ))

    return sorted(anomalies, key=lambda a: -(a.z_score or 0))


# ─── AI text insights ─────────────────────────────────────────────────────────

def _generate_ai_insights(
    income: float,
    expense: float,
    savings_rate: float,
    breakdown: list[CategoryBreakdownItem],
    prediction: Optional[float],
    health_score: int,
    anomaly_count: int,
    budget_statuses: list[BudgetOut],
) -> list[AIInsight]:
    insights: list[AIInsight] = []

    # 1. Savings rate
    if savings_rate >= 20:
        insights.append(AIInsight(
            type="achievement",
            title="Excellent savings discipline!",
            description=f"You're saving {savings_rate:.1f}% of your income — well above the recommended 20%. "
                        "Consider channeling the surplus into index funds or SIPs.",
            impact="positive",
            value=savings_rate,
        ))
    elif savings_rate >= 10:
        insights.append(AIInsight(
            type="tip",
            title="Room to grow your savings",
            description=f"You're saving {savings_rate:.1f}%. Aim for 20% by reviewing your top spending categories.",
            impact="neutral",
            value=savings_rate,
        ))
    else:
        insights.append(AIInsight(
            type="warning",
            title="Low savings rate detected",
            description=f"Only {savings_rate:.1f}% of income is being saved. "
                        "This creates financial vulnerability. Target 20% by cutting discretionary spend.",
            impact="negative",
            value=savings_rate,
        ))

    # 2. Top category overspend
    if breakdown:
        top = breakdown[0]
        if top.pct > 40:
            insights.append(AIInsight(
                type="warning",
                title=f"{top.category_name} dominates your budget",
                description=f"{top.category_name} accounts for {top.pct:.0f}% of expenses. "
                            f"Try the 50/30/20 rule — needs ≤50%, wants ≤30%, savings ≥20%.",
                impact="negative",
                value=float(top.amount),
            ))

    # 3. Budget alerts
    over_budget = [b for b in budget_statuses if b.pct_used >= 90]
    if over_budget:
        names = ", ".join(b.category.name for b in over_budget if b.category)
        insights.append(AIInsight(
            type="warning",
            title=f"Budget nearly exhausted in {len(over_budget)} category(ies)",
            description=f"Spending in {names} has reached ≥90% of budget. "
                        "Pause non-essential purchases in these areas.",
            impact="negative",
        ))

    # 4. Prediction
    if prediction is not None and income > 0:
        delta = prediction - expense
        sign = "up" if delta > 0 else "down"
        insights.append(AIInsight(
            type="prediction",
            title=f"Next month's spending predicted to go {sign}",
            description=f"Based on your spending trend, next month's expenses are projected at "
                        f"${prediction:,.0f} ({'+' if delta>=0 else ''}{delta:,.0f} vs this month). "
                        "Plan accordingly.",
            impact="neutral" if abs(delta) < income * 0.05 else ("negative" if delta > 0 else "positive"),
            value=prediction,
        ))

    # 5. Anomaly flag
    if anomaly_count > 0:
        insights.append(AIInsight(
            type="warning",
            title=f"{anomaly_count} unusual transaction(s) detected",
            description="Some transactions are significantly higher than your typical spending in their category. "
                        "Review the Anomalies section to verify these charges.",
            impact="negative",
            value=anomaly_count,
        ))

    # 6. Health score narrative
    if health_score >= 80:
        insights.append(AIInsight(
            type="achievement",
            title=f"Strong financial health score: {health_score}/100",
            description="Your overall financial health is excellent. Keep maintaining disciplined budgeting.",
            impact="positive",
            value=health_score,
        ))
    elif health_score < 50:
        insights.append(AIInsight(
            type="tip",
            title=f"Financial health needs attention: {health_score}/100",
            description="Focus on building an emergency fund (3–6 months expenses) and reducing high-spend categories.",
            impact="negative",
            value=health_score,
        ))

    return insights


# ─── Main entry point ─────────────────────────────────────────────────────────

async def get_dashboard(
    db: AsyncSession,
    user: User,
    month: int,
    year: int,
) -> AnalyticsDashboard:
    start = date(year, month, 1)
    next_m = month + 1 if month < 12 else 1
    next_y = year if month < 12 else year + 1
    end = date(next_y, next_m, 1) - timedelta(days=1)

    # Fetch this month's transactions
    txs = await _fetch_transactions(db, user.id, start, end)

    income  = sum(float(t.amount) for t in txs if t.type == "income")
    expense = sum(float(t.amount) for t in txs if t.type == "expense")
    savings = income - expense
    savings_rate = (savings / income * 100) if income > 0 else 0.0

    # Category breakdown
    breakdown = _build_category_breakdown(txs)

    # Monthly trend (12 months)
    trend = await _build_monthly_trend(db, user.id)

    # Anomalies (across a broader window — 3 months for more data)
    window_start = (start.replace(day=1) - timedelta(days=90))
    history_txs = await _fetch_transactions(db, user.id, window_start, end)
    anomalies = _detect_anomalies(history_txs)

    # ML prediction
    all_expense_history = await _fetch_all_expense_history(db, user.id)
    prediction = _predict_next_month(all_expense_history)

    # Budget status
    budget_result = await db.execute(
        select(Budget)
        .options(selectinload(Budget.category))
        .where(Budget.user_id == user.id, Budget.month == month, Budget.year == year)
    )
    budgets = list(budget_result.scalars().all())

    budget_statuses: list[BudgetOut] = []
    for b in budgets:
        cat_spent = next(
            (float(item.amount) for item in breakdown if item.category_id == str(b.category_id)),
            0.0,
        )
        pct = (cat_spent / float(b.amount) * 100) if float(b.amount) > 0 else 0
        budget_statuses.append(BudgetOut(
            id=b.id, month=b.month, year=b.year,
            amount=b.amount, alert_at_pct=b.alert_at_pct,
            spent=Decimal(str(round(cat_spent, 2))),
            remaining=Decimal(str(round(max(0, float(b.amount) - cat_spent), 2))),
            pct_used=round(pct, 1),
            category=CategoryOut.model_validate(b.category) if b.category else None,
        ))

    over_budget_count = sum(1 for b in budget_statuses if b.pct_used >= 100)

    # Health score
    health = _health_score(income, expense, savings_rate, over_budget_count, len(anomalies))

    # AI insights
    ai_insights = _generate_ai_insights(
        income, expense, savings_rate, breakdown,
        prediction, health, len(anomalies), budget_statuses,
    )

    return AnalyticsDashboard(
        month=month,
        year=year,
        total_income=Decimal(str(round(income, 2))),
        total_expense=Decimal(str(round(expense, 2))),
        net_savings=Decimal(str(round(savings, 2))),
        savings_rate=round(savings_rate, 2),
        financial_health_score=health,
        category_breakdown=breakdown,
        monthly_trend=trend,
        anomalies=anomalies,
        predicted_next_month=Decimal(str(prediction)) if prediction is not None else None,
        ai_insights=ai_insights,
        budget_status=budget_statuses,
    )
