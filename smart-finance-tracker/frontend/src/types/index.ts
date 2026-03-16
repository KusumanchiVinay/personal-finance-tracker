// frontend/src/types/index.ts

export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  currency: string;
  monthly_income: number;
  avatar_url?: string;
  is_active: boolean;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface Category {
  id: string;
  name: string;
  icon: string;
  color: string;
  type: 'expense' | 'income' | 'both';
  is_system: boolean;
}

export interface Transaction {
  id: string;
  title: string;
  description?: string;
  amount: number;
  type: 'expense' | 'income';
  date: string;
  tags: string[];
  is_recurring: boolean;
  recurrence_rule?: string;
  source: string;
  created_at: string;
  category?: Category;
}

export interface TransactionPage {
  items: Transaction[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface Budget {
  id: string;
  month: number;
  year: number;
  amount: number;
  alert_at_pct: number;
  spent: number;
  remaining: number;
  pct_used: number;
  category?: Category;
}

export interface CategoryBreakdownItem {
  category_id?: string;
  category_name: string;
  icon: string;
  color: string;
  amount: number;
  pct: number;
  tx_count: number;
}

export interface MonthlyTrend {
  year: number;
  month: number;
  income: number;
  expense: number;
  savings: number;
}

export interface AnomalyItem {
  transaction_id: string;
  title: string;
  amount: number;
  date: string;
  reason: string;
  severity: 'low' | 'medium' | 'high';
  z_score?: number;
}

export interface AIInsight {
  type: 'tip' | 'warning' | 'achievement' | 'prediction';
  title: string;
  description: string;
  impact?: 'positive' | 'negative' | 'neutral';
  value?: number;
}

export interface AnalyticsDashboard {
  month: number;
  year: number;
  total_income: number;
  total_expense: number;
  net_savings: number;
  savings_rate: number;
  financial_health_score: number;
  category_breakdown: CategoryBreakdownItem[];
  monthly_trend: MonthlyTrend[];
  anomalies: AnomalyItem[];
  predicted_next_month?: number;
  ai_insights: AIInsight[];
  budget_status: Budget[];
}

export type TransactionFilters = {
  page?: number;
  size?: number;
  type?: 'expense' | 'income';
  category_id?: string;
  start_date?: string;
  end_date?: string;
  search?: string;
};
