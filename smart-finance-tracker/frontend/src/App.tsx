/**
 * App.tsx — root router with protected routes
 */
import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "./store/authStore";
import AuthPage      from "./components/auth/AuthPage";
import Layout        from "./components/shared/Layout";
import Dashboard     from "./components/dashboard/Dashboard";
import TransactionsPage from "./components/transactions/TransactionsPage";
import BudgetPage    from "./components/budget/BudgetPage";
import InsightsPage  from "./components/insights/InsightsPage";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuth } = useAuthStore();
  return isAuth ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<AuthPage />} />
        <Route path="/*" element={
          <ProtectedRoute>
            <Layout>
              <Routes>
                <Route path="/"             element={<Dashboard />} />
                <Route path="/transactions" element={<TransactionsPage />} />
                <Route path="/budget"       element={<BudgetPage />} />
                <Route path="/insights"     element={<InsightsPage />} />
                <Route path="*"             element={<Navigate to="/" replace />} />
              </Routes>
            </Layout>
          </ProtectedRoute>
        } />
      </Routes>
    </BrowserRouter>
  );
}
