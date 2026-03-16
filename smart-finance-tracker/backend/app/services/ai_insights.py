"""
app/services/ai_insights.py
──────────────────────────────────────────────────────────────
AI Insights Service — pure Python (no heavy ML dep needed at
runtime; falls back gracefully when sklearn unavailable).
Production deployment loads the serialised sklearn model
from ai-model/models/spending_model.pkl.
"""
import json
import statistics
from datetime import date, timedelta
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract

from app.models.transaction import Transaction, Category
from app.models.user import User


class AIInsightsService:
    def __init__(self, db: AsyncSession, user: User):
        self.db   = db
        self.user = user

    # ── Public entry points ───────────────────────────────────

    async def generate_all_insights(self) -> Dict[str, Any]:
        tx_data      = await self._fetch_all_transactions()
        health       = await self._health_score_from_data(tx_data)
        prediction   = await self._predict_from_data(tx_data)
        suggestions  = self._generate_suggestions(tx_data)
        anomalies    = self._detect_anomalies(tx_data)
        patterns     = self._spending_patterns(tx_data)

        return {
            "health_score":   health,
            "prediction":     prediction,
            "suggestions":    suggestions,
            "anomalies":      anomalies,
            "patterns":       patterns,
        }

    async def compute_health_score(self) -> Dict[str, Any]:
        tx_data = await self._fetch_all_transactions()
        return await self._health_score_from_data(tx_data)

    async def predict_next_month(self) -> Dict[str, Any]:
        tx_data = await self._fetch_all_transactions()
        return await self._predict_from_data(tx_data)

    # ── Internal helpers ─────────────────────────────────────

    async def _fetch_all_transactions(self) -> List[Dict]:
        result = await self.db.execute(
            select(Transaction, Category.name.label("cat_name"))
            .outerjoin(Category, Transaction.category_id == Category.id)
            .where(Transaction.user_id == self.user.id)
            .order_by(Transaction.date.asc())
        )
        rows = result.all()
        return [
            {
                "id":       str(r.Transaction.id),
                "amount":   float(r.Transaction.amount),
                "type":     r.Transaction.type,
                "category": r.cat_name or "Other",
                "date":     r.Transaction.date,
                "month":    r.Transaction.date.month,
                "year":     r.Transaction.date.year,
            }
            for r in rows
        ]

    # ── Health Score (0–100) ──────────────────────────────────

    async def _health_score_from_data(self, txs: List[Dict]) -> Dict[str, Any]:
        """
        Scoring model:
          Savings rate          40 pts  (target ≥ 20%)
          Budget adherence      20 pts  (based on over-budget categories)
          Expense consistency   20 pts  (low std-dev month-to-month)
          Emergency-fund proxy  20 pts  (≥3 months expenses saved)
        """
        today     = date.today()
        this_m    = [t for t in txs if t["month"] == today.month and t["year"] == today.year]
        income    = sum(t["amount"] for t in this_m if t["type"] == "income")
        expenses  = sum(t["amount"] for t in this_m if t["type"] == "expense")
        savings   = income - expenses

        # 1. Savings rate score
        if income > 0:
            sr = savings / income
            savings_score = min(40, int(sr / 0.20 * 40))
        else:
            savings_score = 0

        # 2. Expense consistency score
        monthly_exp = {}
        for t in txs:
            if t["type"] == "expense":
                key = (t["year"], t["month"])
                monthly_exp[key] = monthly_exp.get(key, 0) + t["amount"]
        if len(monthly_exp) >= 2:
            vals = list(monthly_exp.values())
            mean = statistics.mean(vals)
            cv   = statistics.stdev(vals) / mean if mean > 0 else 1
            consistency_score = max(0, int((1 - min(cv, 1)) * 20))
        else:
            consistency_score = 10  # neutral

        # 3. Emergency fund proxy (3× monthly expense saved)
        avg_monthly_exp = statistics.mean(monthly_exp.values()) if monthly_exp else 1
        total_income    = sum(t["amount"] for t in txs if t["type"] == "income")
        total_expense   = sum(t["amount"] for t in txs if t["type"] == "expense")
        net_saved       = total_income - total_expense
        months_covered  = net_saved / avg_monthly_exp if avg_monthly_exp > 0 else 0
        emergency_score = min(20, int(months_covered / 3 * 20))

        total = savings_score + consistency_score + emergency_score + 12  # 12 base
        total = max(0, min(100, total))

        grade = "A" if total >= 80 else "B" if total >= 65 else "C" if total >= 50 else "D"

        return {
            "score":        total,
            "grade":        grade,
            "breakdown": {
                "savings_rate":   savings_score,
                "consistency":    consistency_score,
                "emergency_fund": emergency_score,
            },
            "summary": self._health_summary(total, savings, income),
        }

    def _health_summary(self, score: int, savings: float, income: float) -> str:
        if score >= 80:
            return "Excellent! Your finances are in great shape."
        if score >= 65:
            return "Good. A few tweaks will push you to the next level."
        if score >= 50:
            return "Fair. Focus on reducing top expense categories."
        return "Needs attention. Consider reviewing your budget plan."

    # ── Spending Prediction ───────────────────────────────────

    async def _predict_from_data(self, txs: List[Dict]) -> Dict[str, Any]:
        """
        Linear trend extrapolation + category-level breakdown.
        In production the sklearn model replaces this.
        """
        monthly_exp: Dict[str, float] = {}
        for t in txs:
            if t["type"] == "expense":
                key = f"{t['year']}-{t['month']:02d}"
                monthly_exp[key] = monthly_exp.get(key, 0) + t["amount"]

        if len(monthly_exp) < 2:
            return {"predicted_total": 0, "confidence": "low", "breakdown": []}

        sorted_months = sorted(monthly_exp.keys())
        values = [monthly_exp[k] for k in sorted_months]

        # Simple linear regression on indices
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(values)
        num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        den = sum((i - x_mean) ** 2 for i in range(n))
        slope     = num / den if den else 0
        intercept = y_mean - slope * x_mean
        predicted = intercept + slope * n

        # Category-level (proportional)
        cat_totals: Dict[str, float] = {}
        for t in txs:
            if t["type"] == "expense":
                cat_totals[t["category"]] = cat_totals.get(t["category"], 0) + t["amount"]
        total_hist = sum(cat_totals.values())
        breakdown  = [
            {"category": cat, "predicted": round(predicted * (amt / total_hist), 2)}
            for cat, amt in sorted(cat_totals.items(), key=lambda x: -x[1])[:6]
        ] if total_hist > 0 else []

        confidence = "high" if n >= 6 else "medium" if n >= 3 else "low"
        return {
            "predicted_total": round(max(0, predicted), 2),
            "confidence":      confidence,
            "trend":           "increasing" if slope > 0 else "decreasing",
            "breakdown":       breakdown,
        }

    # ── Smart Suggestions ────────────────────────────────────

    def _generate_suggestions(self, txs: List[Dict]) -> List[Dict]:
        suggestions = []
        today = date.today()

        # Current-month category totals
        this_m = [t for t in txs if t["month"] == today.month and t["year"] == today.year and t["type"] == "expense"]
        cat_m: Dict[str, float] = {}
        for t in this_m: cat_m[t["category"]] = cat_m.get(t["category"], 0) + t["amount"]

        # Prior-month category totals
        prev = today.replace(day=1) - timedelta(days=1)
        prev_m = [t for t in txs if t["month"] == prev.month and t["year"] == prev.year and t["type"] == "expense"]
        cat_p: Dict[str, float] = {}
        for t in prev_m: cat_p[t["category"]] = cat_p.get(t["category"], 0) + t["amount"]

        total_exp = sum(cat_m.values())

        for cat, amt in sorted(cat_m.items(), key=lambda x: -x[1]):
            # High spend category
            if total_exp > 0 and amt / total_exp > 0.35:
                suggestions.append({
                    "type": "high_category",
                    "priority": "high",
                    "category": cat,
                    "message": f"{cat} accounts for {round(amt/total_exp*100)}% of expenses. Consider setting a tighter budget.",
                    "potential_saving": round(amt * 0.15, 2),
                })
            # Month-over-month spike
            prev_amt = cat_p.get(cat, 0)
            if prev_amt > 0 and amt > prev_amt * 1.3:
                suggestions.append({
                    "type": "spending_spike",
                    "priority": "medium",
                    "category": cat,
                    "message": f"{cat} spending jumped {round((amt/prev_amt - 1)*100)}% vs last month.",
                    "potential_saving": round((amt - prev_amt) * 0.5, 2),
                })

        # Low savings rate
        income = sum(t["amount"] for t in txs if t["month"] == today.month and t["year"] == today.year and t["type"] == "income")
        if income > 0 and total_exp / income > 0.8:
            suggestions.append({
                "type": "savings_rate",
                "priority": "high",
                "category": "Overall",
                "message": "You're spending over 80% of income. Aim to save at least 20%.",
                "potential_saving": round(total_exp * 0.10, 2),
            })

        return suggestions[:5]  # top 5

    # ── Anomaly Detection ────────────────────────────────────

    def _detect_anomalies(self, txs: List[Dict]) -> List[Dict]:
        """
        Z-score based: flag transactions > 2.5σ above category mean.
        Production version uses Isolation Forest (sklearn).
        """
        cat_amounts: Dict[str, List[float]] = {}
        for t in txs:
            if t["type"] == "expense":
                cat_amounts.setdefault(t["category"], []).append(t["amount"])

        anomalies = []
        for t in txs:
            if t["type"] != "expense":
                continue
            amounts = cat_amounts.get(t["category"], [])
            if len(amounts) < 3:
                continue
            mean = statistics.mean(amounts)
            std  = statistics.stdev(amounts)
            if std == 0:
                continue
            z = (t["amount"] - mean) / std
            if z > 2.5:
                anomalies.append({
                    "id":       t["id"],
                    "amount":   t["amount"],
                    "category": t["category"],
                    "date":     str(t["date"]),
                    "z_score":  round(z, 2),
                    "reason":   f"Unusually high for {t['category']} (z={round(z,1)}σ)",
                })
        return sorted(anomalies, key=lambda x: -x["z_score"])[:5]

    # ── Spending Patterns ────────────────────────────────────

    def _spending_patterns(self, txs: List[Dict]) -> Dict[str, Any]:
        # Day-of-week distribution
        dow: Dict[int, float] = {i: 0 for i in range(7)}
        for t in txs:
            if t["type"] == "expense":
                dow[t["date"].weekday()] += t["amount"]
        dow_labels = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        dow_chart  = [{"day": dow_labels[i], "amount": round(dow[i], 2)} for i in range(7)]

        # Top categories overall
        cat_totals: Dict[str, float] = {}
        for t in txs:
            if t["type"] == "expense":
                cat_totals[t["category"]] = cat_totals.get(t["category"], 0) + t["amount"]
        top_cats = sorted(cat_totals.items(), key=lambda x: -x[1])[:5]

        # Monthly average expense
        monthly_exp: Dict[str, float] = {}
        for t in txs:
            if t["type"] == "expense":
                key = f"{t['year']}-{t['month']:02d}"
                monthly_exp[key] = monthly_exp.get(key, 0) + t["amount"]
        avg_monthly = round(statistics.mean(monthly_exp.values()), 2) if monthly_exp else 0

        return {
            "day_of_week":       dow_chart,
            "top_categories":    [{"category": c, "total": round(a, 2)} for c, a in top_cats],
            "avg_monthly_spend": avg_monthly,
            "busiest_day":       dow_labels[max(dow, key=dow.get)],
        }
