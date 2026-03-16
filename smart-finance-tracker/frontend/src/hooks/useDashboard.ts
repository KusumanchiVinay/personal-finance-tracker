/**
 * hooks/useDashboard.ts — dashboard data + AI insights
 */
import { useState, useEffect } from "react";
import { analyticsApi } from "../services/api";

export interface DashboardData {
  month: number;
  year: number;
  income: number;
  expenses: number;
  savings: number;
  savings_rate: number;
  categories: { name: string; icon: string; color: string; amount: number }[];
  monthly_trend: { month: string; income: number; expense: number }[];
  anomalies: { id: string; amount: number; description: string; date: string }[];
}

export interface AIInsights {
  health_score: {
    score: number;
    grade: string;
    breakdown: Record<string, number>;
    summary: string;
  };
  prediction: {
    predicted_total: number;
    confidence: string;
    trend: string;
    breakdown: { category: string; predicted: number }[];
  };
  suggestions: {
    type: string;
    priority: "high" | "medium" | "low";
    category: string;
    message: string;
    potential_saving: number;
  }[];
  anomalies: {
    id: string;
    amount: number;
    category: string;
    date: string;
    z_score: number;
    reason: string;
  }[];
  patterns: {
    day_of_week: { day: string; amount: number }[];
    top_categories: { category: string; total: number }[];
    avg_monthly_spend: number;
    busiest_day: string;
  };
}

export function useDashboard(month: number, year: number) {
  const [data, setData]         = useState<DashboardData | null>(null);
  const [insights, setInsights] = useState<AIInsights | null>(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      analyticsApi.dashboard(month, year),
      analyticsApi.insights(),
    ])
      .then(([db, ins]) => {
        setData(db.data);
        setInsights(ins.data);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [month, year]);

  return { data, insights, loading, error };
}
