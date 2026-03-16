/**
 * hooks/useTransactions.ts — data-fetching + mutation hook
 */
import { useState, useEffect, useCallback } from "react";
import { txApi } from "../services/api";

export interface Transaction {
  id: string;
  amount: number;
  type: "income" | "expense";
  category_id: string;
  category_name: string;
  category_icon: string;
  description: string;
  merchant: string;
  date: string;
  is_recurring: boolean;
  tags: string[];
  is_anomaly: boolean;
  anomaly_score: number | null;
  created_at: string;
}

export interface TransactionFilters {
  page?: number;
  per_page?: number;
  type?: string;
  category_id?: string;
  start_date?: string;
  end_date?: string;
  search?: string;
}

interface PaginatedResult {
  items: Transaction[];
  total: number;
  pages: number;
  page: number;
}

export function useTransactions(filters: TransactionFilters = {}) {
  const [data, setData] = useState<PaginatedResult>({
    items: [], total: 0, pages: 0, page: 1,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchKey = JSON.stringify(filters);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data: d } = await txApi.list(filters);
      setData(d);
    } catch (e: any) {
      setError(e.response?.data?.detail ?? e.message ?? "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [fetchKey]); // eslint-disable-line

  useEffect(() => { fetchData(); }, [fetchData]);

  const create = async (payload: object) => {
    await txApi.create(payload);
    fetchData();
  };

  const update = async (id: string, payload: object) => {
    await txApi.update(id, payload);
    fetchData();
  };

  const remove = async (id: string) => {
    await txApi.remove(id);
    fetchData();
  };

  return { ...data, loading, error, refetch: fetchData, create, update, remove };
}
