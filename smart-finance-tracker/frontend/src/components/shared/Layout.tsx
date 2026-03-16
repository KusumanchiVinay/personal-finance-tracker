/**
 * components/shared/Layout.tsx — App shell with sidebar navigation
 */
import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";

const NAV = [
  { path: "/",             icon: "📊", label: "Dashboard"    },
  { path: "/transactions", icon: "💳", label: "Transactions" },
  { path: "/budget",       icon: "🎯", label: "Budget"       },
  { path: "/insights",     icon: "🤖", label: "AI Insights"  },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const { user, logout } = useAuthStore();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="flex h-screen bg-slate-950 overflow-hidden">
      {/* Sidebar */}
      <aside className={`flex flex-col bg-slate-900 border-r border-slate-800 transition-all duration-300 ${
        collapsed ? "w-16" : "w-60"
      }`}>
        {/* Brand */}
        <div className="flex items-center gap-3 px-4 py-5 border-b border-slate-800">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center shrink-0">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </div>
          {!collapsed && <span className="text-white font-bold text-lg">FinanceAI</span>}
        </div>

        {/* Nav links */}
        <nav className="flex-1 px-2 py-4 space-y-1">
          {NAV.map((n) => {
            const active = location.pathname === n.path;
            return (
              <Link key={n.path} to={n.path}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                  active
                    ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
                    : "text-slate-400 hover:text-white hover:bg-slate-800"
                }`}>
                <span className="text-base shrink-0">{n.icon}</span>
                {!collapsed && <span>{n.label}</span>}
              </Link>
            );
          })}
        </nav>

        {/* User + logout */}
        <div className="px-2 py-4 border-t border-slate-800">
          {!collapsed && user && (
            <div className="px-3 py-2 mb-2">
              <div className="text-white text-sm font-semibold truncate">{user.full_name}</div>
              <div className="text-slate-500 text-xs truncate">{user.email}</div>
            </div>
          )}
          <button onClick={logout}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition`}>
            <span className="shrink-0">🚪</span>
            {!collapsed && "Sign Out"}
          </button>
        </div>

        {/* Collapse toggle */}
        <button onClick={() => setCollapsed(!collapsed)}
          className="mx-2 mb-3 py-2 rounded-xl text-slate-600 hover:text-slate-300 hover:bg-slate-800 transition text-xs text-center">
          {collapsed ? "→" : "←"}
        </button>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-7xl mx-auto p-6">
          {children}
        </div>
      </main>
    </div>
  );
}
