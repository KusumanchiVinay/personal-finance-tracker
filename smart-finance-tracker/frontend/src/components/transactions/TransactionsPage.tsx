/**
 * components/transactions/TransactionsPage.tsx
 * Full transaction history with filtering, add/edit/delete modal
 */
import React, { useState, useEffect } from "react";
import { useTransactions, Transaction } from "../../hooks/useTransactions";
import { categoriesApi, exportApi } from "../../services/api";
import Modal from "../shared/Modal";

interface Category { id: string; name: string; icon: string; color: string; type: string }

const EMPTY_FORM = {
  amount: "", type: "expense", category_id: "", description: "",
  merchant: "", date: new Date().toISOString().split("T")[0],
  is_recurring: false, recur_period: "", tags: "", note: "",
};

export default function TransactionsPage() {
  const [page,   setPage]   = useState(1);
  const [search, setSearch] = useState("");
  const [type,   setType]   = useState("");
  const [catFilter, setCatFilter] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate,   setEndDate]   = useState("");

  const { items, total, pages, loading, create, update, remove } = useTransactions({
    page, per_page: 15, search: search || undefined,
    type: type || undefined, category_id: catFilter || undefined,
    start_date: startDate || undefined, end_date: endDate || undefined,
  });

  const [categories, setCategories] = useState<Category[]>([]);
  const [showModal,  setShowModal]  = useState(false);
  const [editing,    setEditing]    = useState<Transaction | null>(null);
  const [form,       setForm]       = useState(EMPTY_FORM);
  const [saving,     setSaving]     = useState(false);

  useEffect(() => {
    categoriesApi.list().then((r) => setCategories(r.data));
  }, []);

  const openAdd = () => { setEditing(null); setForm(EMPTY_FORM); setShowModal(true); };

  const openEdit = (tx: Transaction) => {
    setEditing(tx);
    setForm({
      amount: String(tx.amount), type: tx.type, category_id: tx.category_id ?? "",
      description: tx.description ?? "", merchant: tx.merchant ?? "", date: tx.date,
      is_recurring: tx.is_recurring, recur_period: "",
      tags: (tx.tags ?? []).join(", "), note: "",
    });
    setShowModal(true);
  };

  const handleSave = async () => {
    setSaving(true);
    const payload = {
      ...form,
      amount: parseFloat(form.amount),
      tags: form.tags ? form.tags.split(",").map((t) => t.trim()).filter(Boolean) : [],
      category_id: form.category_id || undefined,
    };
    try {
      if (editing) await update(editing.id, payload);
      else         await create(payload);
      setShowModal(false);
    } finally { setSaving(false); }
  };

  const handleDelete = async (id: string) => {
    if (confirm("Delete this transaction?")) await remove(id);
  };

  const handleExport = async () => {
    const { data } = await exportApi.csv(startDate, endDate);
    const url = URL.createObjectURL(new Blob([data], { type: "text/csv" }));
    const a = document.createElement("a"); a.href = url; a.download = "transactions.csv"; a.click();
  };

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]; if (!file) return;
    const { data } = await exportApi.importCsv(file);
    alert(`Imported ${data.imported} transactions. ${data.errors?.length ?? 0} errors.`);
    window.location.reload();
  };

  const f = (k: string) => (e: any) =>
    setForm((prev) => ({ ...prev, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value }));

  const filteredCats = categories.filter((c) => !form.type || c.type === form.type);

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Transactions</h1>
          <p className="text-slate-400 text-sm">{total} total records</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <label className="cursor-pointer px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-xl text-sm font-semibold transition">
            📥 Import CSV
            <input type="file" accept=".csv" className="hidden" onChange={handleImport} />
          </label>
          <button onClick={handleExport} className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-xl text-sm font-semibold transition">
            📤 Export CSV
          </button>
          <button onClick={openAdd} className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-semibold shadow-lg shadow-indigo-600/30 transition">
            + Add Transaction
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-4 flex flex-wrap gap-3">
        <input
          placeholder="Search description, merchant..."
          value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className="flex-1 min-w-48 bg-slate-700 border border-slate-600 text-white rounded-xl px-4 py-2 text-sm placeholder-slate-500 focus:outline-none focus:border-indigo-500"
        />
        <select value={type} onChange={(e) => { setType(e.target.value); setPage(1); }}
          className="bg-slate-700 border border-slate-600 text-white rounded-xl px-3 py-2 text-sm">
          <option value="">All Types</option>
          <option value="income">Income</option>
          <option value="expense">Expense</option>
        </select>
        <select value={catFilter} onChange={(e) => { setCatFilter(e.target.value); setPage(1); }}
          className="bg-slate-700 border border-slate-600 text-white rounded-xl px-3 py-2 text-sm">
          <option value="">All Categories</option>
          {categories.map((c) => <option key={c.id} value={c.id}>{c.icon} {c.name}</option>)}
        </select>
        <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)}
          className="bg-slate-700 border border-slate-600 text-white rounded-xl px-3 py-2 text-sm" />
        <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)}
          className="bg-slate-700 border border-slate-600 text-white rounded-xl px-3 py-2 text-sm" />
      </div>

      {/* Table */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-500">Loading…</div>
        ) : items.length === 0 ? (
          <div className="p-12 text-center">
            <div className="text-4xl mb-3">📭</div>
            <p className="text-slate-400">No transactions found. Add your first one!</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="border-b border-slate-700">
              <tr className="text-slate-400 text-xs uppercase tracking-wider">
                <th className="text-left px-5 py-4">Date</th>
                <th className="text-left px-5 py-4">Description</th>
                <th className="text-left px-5 py-4">Category</th>
                <th className="text-right px-5 py-4">Amount</th>
                <th className="text-center px-5 py-4">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {items.map((tx) => (
                <tr key={tx.id} className="hover:bg-slate-700/30 transition group">
                  <td className="px-5 py-4 text-slate-400 whitespace-nowrap">{tx.date}</td>
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-2">
                      {tx.is_anomaly && <span title="Unusual" className="text-amber-400 text-xs">⚠️</span>}
                      <span className="text-white font-medium">{tx.description || tx.merchant || "—"}</span>
                    </div>
                    {tx.merchant && tx.description && (
                      <div className="text-slate-500 text-xs mt-0.5">{tx.merchant}</div>
                    )}
                  </td>
                  <td className="px-5 py-4">
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-700 text-slate-300">
                      {tx.category_icon} {tx.category_name ?? "—"}
                    </span>
                  </td>
                  <td className={`px-5 py-4 text-right font-bold tabular-nums ${
                    tx.type === "income" ? "text-emerald-400" : "text-red-400"
                  }`}>
                    {tx.type === "income" ? "+" : "-"}${tx.amount.toLocaleString()}
                  </td>
                  <td className="px-5 py-4 text-center">
                    <div className="flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100 transition">
                      <button onClick={() => openEdit(tx)}
                        className="p-1.5 rounded-lg bg-indigo-600/20 text-indigo-400 hover:bg-indigo-600/40 transition text-xs">
                        ✏️
                      </button>
                      <button onClick={() => handleDelete(tx.id)}
                        className="p-1.5 rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/40 transition text-xs">
                        🗑️
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {pages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button disabled={page === 1} onClick={() => setPage(page - 1)}
            className="px-4 py-2 bg-slate-800 border border-slate-700 text-white rounded-xl text-sm disabled:opacity-40 hover:bg-slate-700 transition">
            ← Prev
          </button>
          <span className="text-slate-400 text-sm">Page {page} of {pages}</span>
          <button disabled={page === pages} onClick={() => setPage(page + 1)}
            className="px-4 py-2 bg-slate-800 border border-slate-700 text-white rounded-xl text-sm disabled:opacity-40 hover:bg-slate-700 transition">
            Next →
          </button>
        </div>
      )}

      {/* Add/Edit Modal */}
      <Modal open={showModal} onClose={() => setShowModal(false)}
        title={editing ? "Edit Transaction" : "Add Transaction"}>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Amount</label>
              <input type="number" step="0.01" value={form.amount} onChange={f("amount")} placeholder="0.00"
                className="mt-1 w-full bg-slate-700 border border-slate-600 text-white rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500" />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Type</label>
              <select value={form.type} onChange={f("type")}
                className="mt-1 w-full bg-slate-700 border border-slate-600 text-white rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500">
                <option value="expense">Expense</option>
                <option value="income">Income</option>
              </select>
            </div>
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Category</label>
            <select value={form.category_id} onChange={f("category_id")}
              className="mt-1 w-full bg-slate-700 border border-slate-600 text-white rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500">
              <option value="">— Select category —</option>
              {filteredCats.map((c) => <option key={c.id} value={c.id}>{c.icon} {c.name}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Description</label>
            <input type="text" value={form.description} onChange={f("description")} placeholder="What was it for?"
              className="mt-1 w-full bg-slate-700 border border-slate-600 text-white rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Merchant</label>
              <input type="text" value={form.merchant} onChange={f("merchant")} placeholder="Amazon, Uber…"
                className="mt-1 w-full bg-slate-700 border border-slate-600 text-white rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500" />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Date</label>
              <input type="date" value={form.date} onChange={f("date")}
                className="mt-1 w-full bg-slate-700 border border-slate-600 text-white rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500" />
            </div>
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Tags (comma-separated)</label>
            <input type="text" value={form.tags} onChange={f("tags")} placeholder="groceries, work, travel"
              className="mt-1 w-full bg-slate-700 border border-slate-600 text-white rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500" />
          </div>
          <label className="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" checked={form.is_recurring} onChange={f("is_recurring")}
              className="w-4 h-4 rounded text-indigo-600" />
            <span className="text-sm text-slate-300">Recurring transaction</span>
          </label>
          <div className="flex gap-3 pt-2">
            <button onClick={handleSave} disabled={saving}
              className="flex-1 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-semibold text-sm transition disabled:opacity-50">
              {saving ? "Saving…" : editing ? "Save Changes" : "Add Transaction"}
            </button>
            <button onClick={() => setShowModal(false)}
              className="px-5 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-xl font-semibold text-sm transition">
              Cancel
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
