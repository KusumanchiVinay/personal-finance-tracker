/**
 * components/insights/InsightsPage.tsx
 * Full AI Insights panel — health score, predictions, suggestions, anomalies, patterns
 */
import React from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis } from "recharts";
import { useDashboard } from "../../hooks/useDashboard";
import HealthScoreRing from "./HealthScoreRing";
import Spinner from "../shared/Spinner";

const PRIORITY_STYLE: Record<string, string> = {
  high:   "border-red-500/40 bg-red-500/10",
  medium: "border-amber-500/40 bg-amber-500/10",
  low:    "border-blue-500/40 bg-blue-500/10",
};
const PRIORITY_BADGE: Record<string, string> = {
  high:   "bg-red-500/20 text-red-400",
  medium: "bg-amber-500/20 text-amber-400",
  low:    "bg-blue-500/20 text-blue-400",
};

export default function InsightsPage() {
  const today = new Date();
  const { insights, loading } = useDashboard(today.getMonth() + 1, today.getFullYear());

  if (loading) return <Spinner />;

  if (!insights) return (
    <div className="flex flex-col items-center justify-center h-64 text-center">
      <div className="text-5xl mb-4">🤖</div>
      <p className="text-white font-semibold text-lg">AI Insights Unavailable</p>
      <p className="text-slate-400 mt-2">Add at least 5 transactions to generate insights.</p>
    </div>
  );

  const { health_score, prediction, suggestions, anomalies, patterns } = insights;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">AI Financial Insights</h1>
        <p className="text-slate-400 mt-1">Powered by machine learning analysis of your spending patterns</p>
      </div>

      {/* Top row: health + prediction */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Health Score */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
          <h3 className="text-white font-semibold mb-5">Financial Health Score</h3>
          <div className="flex items-center gap-8">
            <HealthScoreRing score={health_score.score} grade={health_score.grade} size={140} />
            <div className="flex-1 space-y-3">
              {Object.entries(health_score.breakdown).map(([key, val]) => (
                <div key={key}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-400 capitalize">{key.replace(/_/g, " ")}</span>
                    <span className="text-white font-semibold">{val as number}/40</span>
                  </div>
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 rounded-full transition-all"
                      style={{ width: `${Math.min(100, ((val as number) / 40) * 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
          <p className="mt-5 text-slate-300 text-sm bg-slate-700/50 rounded-xl p-3">{health_score.summary}</p>
        </div>

        {/* Prediction */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
          <h3 className="text-white font-semibold mb-2">Next Month Prediction</h3>
          <div className="flex items-center gap-3 mb-5">
            <span className={`text-xs px-2 py-1 rounded-full font-semibold ${
              prediction.confidence === "high" ? "bg-emerald-500/20 text-emerald-400" :
              prediction.confidence === "medium" ? "bg-amber-500/20 text-amber-400" :
              "bg-slate-600 text-slate-400"
            }`}>
              {prediction.confidence} confidence
            </span>
            <span className={`text-xs px-2 py-1 rounded-full font-semibold ${
              prediction.trend === "increasing" ? "bg-red-500/20 text-red-400" : "bg-emerald-500/20 text-emerald-400"
            }`}>
              {prediction.trend === "increasing" ? "📈 Trending up" : "📉 Trending down"}
            </span>
          </div>
          <div className="text-center mb-5">
            <div className="text-4xl font-bold text-white">${prediction.predicted_total.toLocaleString()}</div>
            <div className="text-slate-400 text-sm mt-1">Predicted total expenses</div>
          </div>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={prediction.breakdown}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="category" tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} tickFormatter={(v) => `$${v}`} />
              <Tooltip formatter={(v: number) => [`$${v}`, "Predicted"]}
                contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                labelStyle={{ color: "#e2e8f0" }} />
              <Bar dataKey="predicted" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Smart Suggestions */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
        <h3 className="text-white font-semibold mb-5">💡 Smart Suggestions</h3>
        {suggestions?.length ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {suggestions.map((s, i) => (
              <div key={i} className={`border rounded-xl p-4 ${PRIORITY_STYLE[s.priority]}`}>
                <div className="flex items-start justify-between mb-2">
                  <span className="text-white font-semibold text-sm">{s.category}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${PRIORITY_BADGE[s.priority]}`}>
                    {s.priority}
                  </span>
                </div>
                <p className="text-slate-300 text-sm leading-relaxed">{s.message}</p>
                {s.potential_saving > 0 && (
                  <p className="mt-2 text-emerald-400 text-xs font-semibold">
                    💰 Potential saving: ${s.potential_saving.toLocaleString()}
                  </p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-slate-500 text-sm">Your spending looks healthy! No suggestions right now.</p>
        )}
      </div>

      {/* Spending Patterns */}
      {patterns && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
            <h3 className="text-white font-semibold mb-1">Spending by Day of Week</h3>
            <p className="text-slate-400 text-xs mb-4">Busiest day: <span className="text-indigo-400">{patterns.busiest_day}</span></p>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={patterns.day_of_week}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="day" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} tickFormatter={(v) => `$${v}`} />
                <Tooltip formatter={(v: number) => [`$${v}`, "Spent"]}
                  contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }} />
                <Bar dataKey="amount" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
            <h3 className="text-white font-semibold mb-1">Top Spending Categories</h3>
            <p className="text-slate-400 text-xs mb-4">Monthly average: <span className="text-indigo-400">${patterns.avg_monthly_spend.toLocaleString()}</span></p>
            <div className="space-y-3">
              {patterns.top_categories.map((c, i) => {
                const max = patterns.top_categories[0]?.total ?? 1;
                return (
                  <div key={c.category}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-300">{c.category}</span>
                      <span className="text-white font-semibold">${c.total.toLocaleString()}</span>
                    </div>
                    <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${(c.total / max) * 100}%`,
                          background: `hsl(${240 + i * 30}, 70%, 60%)`,
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Anomalies */}
      {anomalies?.length > 0 && (
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
          <h3 className="text-white font-semibold mb-5">⚠️ Anomaly Detection</h3>
          <p className="text-slate-400 text-sm mb-4">
            These transactions are statistically unusual compared to your spending patterns.
          </p>
          <div className="space-y-3">
            {anomalies.map((a, i) => (
              <div key={i} className="flex items-center justify-between p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl">
                <div>
                  <div className="text-white font-semibold text-sm">{a.category} — {a.date}</div>
                  <div className="text-slate-400 text-xs mt-0.5">{a.reason}</div>
                </div>
                <div className="text-right">
                  <div className="text-amber-400 font-bold">${a.amount.toLocaleString()}</div>
                  <div className="text-slate-500 text-xs">z-score: {a.z_score}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
