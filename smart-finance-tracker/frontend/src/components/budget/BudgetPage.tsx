/**
 * components/budget/BudgetPage.tsx
 * Monthly budget planning with live spend tracking
 */
import React, { useState, useEffect } from "react";
import { budgetsApi, categoriesApi } from "../../services/api";

interface Budget {
  id: string; category_id: string; category_name: string; category_icon: string;
  amount: number; spent: number; pct_used: number; alert_at: number;
}
interface Category { id: string; name: string; icon: string; type: string }

export default function BudgetPage() {
  const today = new Date();
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [year,  setYear]  = useState(today.getFullYear());
  const [budgets, setBudgets]     = useState<Budget[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading]     = useState(false);
  const [form, setForm] = useState({ category_id: "", amount: "", alert_at: "80" });
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [b, c] = await Promise.all([budgetsApi.list(month, year), categoriesApi.list()]);
      setBudgets(b.data); setCategories(c.data.filter((x: Category) => x.type === "expense"));
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [month, year]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.category_id || !form.amount) return;
    setSaving(true);
    await budgetsApi.create({
      category_id: form.category_id, amount: parseFloat(form.amount),
      alert_at: parseFloat(form.alert_at), period: "monthly", month, year,
    });
    setForm({ category_id: "", amount: "", alert_at: "80" });
    await load();
    setSaving(false);
  };

  const handleDelete = async (id: string) => {
    await budgetsApi.remove(id); load();
  };

  const totalBudget = budgets.reduce((s, b) => s + b.amount, 0);
  const totalSpent  = budgets.reduce((s, b) => s + b.spent,  0);
  const overBudget  = budgets.filter((b) => b.pct_used > 100).length;
  const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Budget Planner</h1>
          <p className="text-slate-400 text-sm">Set and track monthly category budgets</p>
        </div>
        <div className="flex gap-2">
          <select value={month} onChange={(e) => setMonth(+e.target.value)}
            className="bg-slate-800 border border-slate-700 text-white rounded-xl px-3 py-2 text-sm">
            {MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
          </select>
          <select value={year} onChange={(e) => setYear(+e.target.value)}
            className="bg-slate-800 border border-slate-700 text-white rounded-xl px-3 py-2 text-sm">
            {[2024, 2025, 2026].map((y) => <option key={y}>{y}</option>)}
          </select>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5 text-center">
          <div className="text-2xl font-bold text-white">${totalBudget.toLocaleString()}</div>
          <div className="text-slate-400 text-sm mt-1">Total Budget</div>
        </div>
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5 text-center">
          <div className="text-2xl font-bold text-white">${totalSpent.toLocaleString()}</div>
          <div className="text-slate-400 text-sm mt-1">Total Spent</div>
        </div>
        <div className={`border rounded-2xl p-5 text-center ${
          overBudget > 0 ? "bg-red-500/10 border-red-500/30" : "bg-emerald-500/10 border-emerald-500/30"
        }`}>
          <div className={`text-2xl font-bold ${overBudget > 0 ? "text-red-400" : "text-emerald-400"}`}>
            {overBudget}
          </div>
          <div className="text-slate-400 text-sm mt-1">Over Budget</div>
        </div>
      </div>

      {/* Overall progress */}
      {totalBudget > 0 && (
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5">
          <div className="flex justify-between text-sm mb-2">
            <span className="text-slate-300 font-semibold">Overall budget usage</span>
            <span className="text-white font-bold">{Math.round(totalSpent / totalBudget * 100)}%</span>
          </div>
          <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all"
              style={{
                width: `${Math.min(100, totalSpent / totalBudget * 100)}%`,
                background: totalSpent / totalBudget > 0.9 ? "#ef4444" :
                            totalSpent / totalBudget > 0.7 ? "#f59e0b" : "#10b981",
              }}
            />
          </div>
        </div>
      )}

      {/* Budget list */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl overflow-hidden">
        {loading ? (
          <div className="p-10 text-center text-slate-500">Loading…</div>
        ) : budgets.length === 0 ? (
          <div className="p-10 text-center">
            <div className="text-4xl mb-3">🎯</div>
            <p className="text-slate-400">No budgets set for this month. Add one below!</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-700/50">
            {budgets.map((b) => {
              const over     = b.pct_used > 100;
              const warning  = b.pct_used >= b.alert_at && !over;
              const barColor = over ? "#ef4444" : warning ? "#f59e0b" : "#10b981";
              const remaining = b.amount - b.spent;
              return (
                <div key={b.id} className="px-6 py-5">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <span className="text-white font-semibold">
                        {b.category_icon} {b.category_name}
                      </span>
                      {over && <span className="ml-2 text-xs px-2 py-0.5 bg-red-500/20 text-red-400 rounded-full font-semibold">Over budget!</span>}
                      {warning && <span className="ml-2 text-xs px-2 py-0.5 bg-amber-500/20 text-amber-400 rounded-full font-semibold">⚠️ Nearing limit</span>}
                    </div>
                    <button onClick={() => handleDelete(b.id)}
                      className="text-slate-600 hover:text-red-400 transition text-sm">✕</button>
                  </div>
                  <div className="h-2.5 bg-slate-700 rounded-full overflow-hidden mb-2">
                    <div className="h-full rounded-full transition-all" style={{ width: `${Math.min(100, b.pct_used)}%`, background: barColor }} />
                  </div>
                  <div className="flex justify-between text-xs text-slate-400">
                    <span>${b.spent.toLocaleString()} spent</span>
                    <span>{Math.round(b.pct_used)}% of ${b.amount.toLocaleString()}</span>
                    <span className={remaining >= 0 ? "text-emerald-400" : "text-red-400"}>
                      {remaining >= 0 ? `$${remaining.toLocaleString()} left` : `$${Math.abs(remaining).toLocaleString()} over`}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Add budget form */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
        <h3 className="text-white font-semibold mb-4">Add Budget</h3>
        <form onSubmit={handleAdd} className="grid grid-cols-1 sm:grid-cols-4 gap-4 items-end">
          <div>
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Category</label>
            <select value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })} required
              className="w-full bg-slate-700 border border-slate-600 text-white rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500">
              <option value="">Select…</option>
              {categories.map((c) => <option key={c.id} value={c.id}>{c.icon} {c.name}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Budget Amount ($)</label>
            <input type="number" step="0.01" value={form.amount}
              onChange={(e) => setForm({ ...form, amount: e.target.value })} placeholder="500.00" required
              className="w-full bg-slate-700 border border-slate-600 text-white rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500" />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Alert at (%)</label>
            <input type="number" min="1" max="100" value={form.alert_at}
              onChange={(e) => setForm({ ...form, alert_at: e.target.value })}
              className="w-full bg-slate-700 border border-slate-600 text-white rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500" />
          </div>
          <button type="submit" disabled={saving}
            className="py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-semibold text-sm shadow-lg shadow-indigo-600/30 transition disabled:opacity-50">
            {saving ? "Adding…" : "+ Set Budget"}
          </button>
        </form>
      </div>
    </div>
  );
}
