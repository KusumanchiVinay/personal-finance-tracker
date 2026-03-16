/**
 * components/dashboard/Dashboard.tsx
 * Main financial dashboard — summary cards + charts + AI insights preview
 */
import React, { useState } from "react";
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { useDashboard } from "../../hooks/useDashboard";
import { useAuthStore } from "../../store/authStore";
import HealthScoreRing from "../insights/HealthScoreRing";
import Spinner from "../shared/Spinner";

const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const PIE_COLORS = ["#6366f1","#8b5cf6","#a78bfa","#06b6d4","#10b981","#f59e0b","#f97316","#ef4444"];

function MetricCard({ label, value, delta, deltaPositive, icon, color }: any) {
  return (
    <div className={`relative overflow-hidden rounded-2xl p-6 border border-slate-700/50 bg-slate-800/50 backdrop-blur`}>
      <div className={`absolute top-0 right-0 w-24 h-24 rounded-full blur-2xl opacity-20 ${color}`} />
      <div className="flex items-start justify-between mb-4">
        <span className="text-2xl">{icon}</span>
        {delta !== undefined && (
          <span className={`text-xs font-semibold px-2 py-1 rounded-full ${
            deltaPositive ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"
          }`}>
            {deltaPositive ? "↑" : "↓"} {Math.abs(delta)}%
          </span>
        )}
      </div>
      <div className="text-2xl font-bold text-white mb-1">{value}</div>
      <div className="text-sm text-slate-400">{label}</div>
    </div>
  );
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-3 shadow-xl text-sm">
      <p className="text-slate-300 mb-2 font-semibold">{label}</p>
      {payload.map((p: any) => (
        <p key={p.name} style={{ color: p.color }}>
          {p.name}: ${p.value?.toLocaleString()}
        </p>
      ))}
    </div>
  );
}

export default function Dashboard() {
  const today = new Date();
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [year,  setYear]  = useState(today.getFullYear());
  const { data, insights, loading } = useDashboard(month, year);
  const { user } = useAuthStore();

  const fmt = (n: number) => {
    const sym = user?.currency === "INR" ? "₹" : "$";
    return `${sym}${n?.toLocaleString("en-IN", { maximumFractionDigits: 0 }) ?? 0}`;
  };

  if (loading) return <Spinner />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">
            Good {today.getHours() < 12 ? "morning" : today.getHours() < 17 ? "afternoon" : "evening"},&nbsp;
            {user?.full_name?.split(" ")[0]} 👋
          </h1>
          <p className="text-slate-400 mt-1">Here's your financial overview</p>
        </div>
        <div className="flex gap-2">
          <select
            value={month}
            onChange={(e) => setMonth(+e.target.value)}
            className="bg-slate-800 border border-slate-700 text-white rounded-xl px-3 py-2 text-sm"
          >
            {MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
          </select>
          <select
            value={year}
            onChange={(e) => setYear(+e.target.value)}
            className="bg-slate-800 border border-slate-700 text-white rounded-xl px-3 py-2 text-sm"
          >
            {[2023, 2024, 2025, 2026].map((y) => <option key={y}>{y}</option>)}
          </select>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard icon="💰" label="Total Income"   value={fmt(data?.income   ?? 0)} color="bg-emerald-500" deltaPositive />
        <MetricCard icon="💳" label="Total Expenses" value={fmt(data?.expenses ?? 0)} color="bg-red-500" deltaPositive={false} />
        <MetricCard icon="🏦" label="Net Savings"    value={fmt(data?.savings  ?? 0)} color="bg-indigo-500" deltaPositive={(data?.savings ?? 0) >= 0} />
        <MetricCard icon="📊" label="Savings Rate"   value={`${data?.savings_rate ?? 0}%`} color="bg-violet-500" deltaPositive={(data?.savings_rate ?? 0) >= 20} />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Monthly trend — 2 cols */}
        <div className="lg:col-span-2 bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
          <h3 className="text-white font-semibold mb-6">Income vs Expenses Trend</h3>
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={data?.monthly_trend ?? []}>
              <defs>
                <linearGradient id="gIncome" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#10b981" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gExpense" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#6366f1" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="month" tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} tickFormatter={(v) => `$${v / 1000}k`} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ color: "#94a3b8", fontSize: 12 }} />
              <Area type="monotone" dataKey="income"  stroke="#10b981" fill="url(#gIncome)"  strokeWidth={2} name="Income" />
              <Area type="monotone" dataKey="expense" stroke="#6366f1" fill="url(#gExpense)" strokeWidth={2} name="Expense" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Donut chart */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
          <h3 className="text-white font-semibold mb-4">Spending by Category</h3>
          {data?.categories?.length ? (
            <>
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie
                    data={data.categories}
                    dataKey="amount"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={3}
                  >
                    {data.categories.map((_: any, i: number) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v: number) => fmt(v)} />
                </PieChart>
              </ResponsiveContainer>
              <div className="mt-3 space-y-2">
                {data.categories.slice(0, 4).map((c: any, i: number) => (
                  <div key={c.name} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full" style={{ background: PIE_COLORS[i % PIE_COLORS.length] }} />
                      <span className="text-slate-300">{c.icon} {c.name}</span>
                    </div>
                    <span className="text-slate-400">{fmt(c.amount)}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="text-slate-500 text-sm text-center mt-12">No expense data yet</p>
          )}
        </div>
      </div>

      {/* Bottom row: bar chart + health score + top suggestion */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Day-of-week pattern */}
        <div className="lg:col-span-2 bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
          <h3 className="text-white font-semibold mb-6">Spending by Day of Week</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={insights?.patterns?.day_of_week ?? []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="day" tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} tickFormatter={(v) => `$${v}`} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="amount" name="Spent" fill="#6366f1" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Health Score */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6 flex flex-col items-center justify-center">
          <h3 className="text-white font-semibold mb-4">Financial Health</h3>
          {insights?.health_score ? (
            <>
              <HealthScoreRing score={insights.health_score.score} grade={insights.health_score.grade} />
              <p className="text-slate-400 text-sm text-center mt-4">{insights.health_score.summary}</p>
            </>
          ) : (
            <p className="text-slate-500 text-sm">Add transactions to see your score</p>
          )}
        </div>
      </div>

      {/* Anomaly alerts */}
      {data?.anomalies?.length > 0 && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-2xl p-5">
          <h3 className="text-amber-400 font-semibold mb-3">⚠️ Unusual Transactions Detected</h3>
          <div className="space-y-2">
            {data.anomalies.map((a: any) => (
              <div key={a.id} className="flex items-center justify-between text-sm">
                <span className="text-slate-300">{a.description ?? "Transaction"} — {a.date}</span>
                <span className="text-amber-400 font-semibold">{fmt(a.amount)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
