# 🚀 Smart Personal Finance Tracker with AI Insights

A production-ready full-stack web application featuring JWT authentication,
full expense CRUD, ML-powered spending predictions, anomaly detection, and a
real-time financial health score.

---

## 📁 Project Structure

```
smart-finance-tracker/
│
├── frontend/                        # React + Vite + Tailwind CSS
│   ├── src/
│   │   ├── App.tsx                  # Root router
│   │   ├── main.tsx                 # Entry point
│   │   ├── index.css                # Tailwind + global styles
│   │   ├── components/
│   │   │   ├── auth/
│   │   │   │   └── AuthPage.tsx     # Login / Register
│   │   │   ├── dashboard/
│   │   │   │   └── Dashboard.tsx    # Main dashboard + charts
│   │   │   ├── transactions/
│   │   │   │   └── TransactionsPage.tsx  # CRUD + CSV
│   │   │   ├── budget/
│   │   │   │   └── BudgetPage.tsx   # Budget planner
│   │   │   ├── insights/
│   │   │   │   ├── InsightsPage.tsx # AI insights panel
│   │   │   │   └── HealthScoreRing.tsx   # SVG health gauge
│   │   │   └── shared/
│   │   │       ├── Layout.tsx       # Sidebar shell
│   │   │       ├── Modal.tsx        # Reusable modal
│   │   │       └── Spinner.tsx      # Loading state
│   │   ├── hooks/
│   │   │   ├── useTransactions.ts   # Data-fetching + mutations
│   │   │   └── useDashboard.ts      # Dashboard + AI insights
│   │   ├── services/
│   │   │   └── api.ts               # Axios + JWT interceptors
│   │   └── store/
│   │       └── authStore.ts         # Zustand auth state
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── Dockerfile
│   └── nginx.conf
│
├── backend/                         # Python FastAPI
│   ├── main.py                      # App entry point
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env.example
│   └── app/
│       ├── api/v1/
│       │   ├── router.py            # Master router
│       │   └── endpoints/
│       │       ├── auth.py          # Register / Login / Refresh
│       │       ├── transactions.py  # Full CRUD + filters
│       │       ├── categories.py    # Category management
│       │       ├── budgets.py       # Budget CRUD + spend tracking
│       │       ├── analytics.py     # Dashboard + AI endpoints
│       │       └── export.py        # CSV import / export
│       ├── core/
│       │   ├── config.py            # Pydantic settings
│       │   ├── security.py          # JWT + bcrypt
│       │   └── deps.py              # FastAPI dependencies
│       ├── db/
│       │   └── session.py           # Async SQLAlchemy engine
│       ├── models/
│       │   ├── user.py              # User ORM model
│       │   ├── transaction.py       # Transaction + Category + Budget
│       │   └── mixins.py            # Timestamp mixin
│       ├── schemas/
│       │   ├── auth.py              # Auth request/response
│       │   ├── transaction.py       # Transaction schemas
│       │   └── budget.py            # Budget schemas
│       └── services/
│           └── ai_insights.py       # AI: health score, prediction, anomalies
│
├── ai-model/                        # Machine Learning pipeline
│   ├── spending_predictor.py        # Train + inference (sklearn)
│   ├── requirements.txt
│   └── models/                      # Serialised .pkl files (gitignored)
│
├── database/
│   ├── schema.sql                   # Full PostgreSQL schema + views + triggers
│   ├── migrations/
│   │   └── env.py                   # Alembic async env
│   └── seeds/
│       └── seed_data.py             # Demo data seeder
│
└── docker-compose.yml               # Full stack (db + redis + backend + frontend)
```

---

## ⚙️ Quick Start (Docker — recommended)

```bash
# 1. Clone and enter the project
git clone <your-repo-url> smart-finance-tracker
cd smart-finance-tracker

# 2. Copy env file
cp backend/.env.example backend/.env
# Edit backend/.env — set a strong SECRET_KEY

# 3. Start everything
docker compose up --build -d

# 4. Seed sample data (optional)
docker compose exec backend python ../database/seeds/seed_data.py

# 5. Open the app
open http://localhost:3000

# API docs (development only)
open http://localhost:8000/docs
```

Demo credentials (after seeding):
- **Email:** demo@financeai.com
- **Password:** Demo@1234

---

## 🛠️ Manual Development Setup

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up PostgreSQL
createdb finance_db
psql finance_db < ../database/schema.sql

# Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL and SECRET_KEY

# Run development server
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

npm install
cp .env.example .env.local    # set VITE_API_URL=http://localhost:8000/api/v1

npm run dev     # → http://localhost:5173
```

### Train ML Models (optional)

```bash
cd ai-model
pip install -r requirements.txt

# Export your transactions as CSV first:
# curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/export/csv > data/transactions.csv

python spending_predictor.py --train --data data/transactions.csv
```

---

## 🔌 REST API Reference

### Authentication
| Method | Endpoint                  | Description              |
|--------|---------------------------|-----------------------------|
| POST   | `/api/v1/auth/register`   | Create account           |
| POST   | `/api/v1/auth/login`      | Get JWT tokens           |
| POST   | `/api/v1/auth/refresh`    | Refresh access token     |
| GET    | `/api/v1/auth/me`         | Current user profile     |

### Transactions
| Method | Endpoint                        | Description                   |
|--------|---------------------------------|-------------------------------|
| GET    | `/api/v1/transactions`          | List (paginated + filterable) |
| POST   | `/api/v1/transactions`          | Create transaction            |
| GET    | `/api/v1/transactions/{id}`     | Get single transaction        |
| PATCH  | `/api/v1/transactions/{id}`     | Update transaction            |
| DELETE | `/api/v1/transactions/{id}`     | Delete transaction            |

Query params: `page`, `per_page`, `type`, `category_id`, `start_date`, `end_date`, `search`

### Analytics & AI
| Method | Endpoint                        | Description                              |
|--------|---------------------------------|------------------------------------------|
| GET    | `/api/v1/analytics/dashboard`   | Summary cards + trend + category split   |
| GET    | `/api/v1/analytics/insights`    | Full AI: health score, prediction, etc.  |
| GET    | `/api/v1/analytics/health-score`| Financial health score (0–100)           |
| GET    | `/api/v1/analytics/prediction`  | Next-month spend prediction              |

### Budgets
| Method | Endpoint               | Description                |
|--------|------------------------|----------------------------|
| GET    | `/api/v1/budgets`      | List budgets with % used   |
| POST   | `/api/v1/budgets`      | Create budget              |
| DELETE | `/api/v1/budgets/{id}` | Delete budget              |

### Export
| Method | Endpoint               | Description           |
|--------|------------------------|-----------------------|
| GET    | `/api/v1/export/csv`   | Download CSV export   |
| POST   | `/api/v1/export/csv`   | Upload CSV import     |

---

## 🤖 AI Features Explained

### Financial Health Score (0–100)
Composite score across three dimensions:

| Component        | Weight | Metric                            |
|------------------|--------|-----------------------------------|
| Savings Rate     | 40 pts | Target: save ≥ 20% of income     |
| Expense Consistency | 20 pts | Low month-to-month variance    |
| Emergency Fund   | 20 pts | ≥ 3 months expenses saved        |
| Base              | 12 pts | Always awarded                   |

Grade scale: A (80+), B (65+), C (50+), D (<50)

### Spending Prediction
- **Algorithm:** Ridge Regression with time-series cross-validation
- **Features:** 3-month lags, rolling mean/std, transaction count/avg, cyclical month encoding
- **Training:** `TimeSeriesSplit` with 5 folds — prevents data leakage
- **Output:** Total predicted spend + per-category breakdown + confidence level

### Anomaly Detection
- **Development fallback:** Z-score (flags transactions > 2.5σ above category mean)
- **Production:** Isolation Forest (sklearn) — trains on `[amount, z_score]` feature space
  with 5% contamination rate
- **Retrain trigger:** Run `spending_predictor.py --train` on new data exports

### Smart Suggestions
Rule-based engine that checks:
1. Any category consuming > 35% of total expenses
2. Month-over-month category spend spikes > 30%
3. Overall savings rate below 20%

---

## 🗄️ Database Schema

Key tables and relationships:

```
users
  └── transactions  (user_id → users.id)
        └── categories (category_id → categories.id)
  └── budgets       (user_id → users.id, category_id → categories.id)
  └── analytics_cache (user_id → users.id)
  └── refresh_tokens  (user_id → users.id)
```

Useful views pre-built in schema:
- `v_monthly_summary` — aggregated income/expense per user/month/category
- `v_category_budget_status` — live budget utilisation percentages

---

## 🔒 Security

- Passwords hashed with **bcrypt** (12 rounds)
- JWT access tokens expire in **30 minutes**
- Refresh tokens expire in **7 days**
- All endpoints protected by `HTTPBearer` dependency
- CORS restricted to `ALLOWED_ORIGINS` env variable
- Production mode disables `/docs` and `/redoc` endpoints

---

## 🚀 Production Deployment Checklist

- [ ] Set `ENVIRONMENT=production` in backend `.env`
- [ ] Generate strong `SECRET_KEY`: `python -c "import secrets; print(secrets.token_hex(32))"`
- [ ] Set `ALLOWED_ORIGINS` to your actual frontend domain
- [ ] Enable HTTPS (Nginx + Let's Encrypt / Cloudflare)
- [ ] Set up PostgreSQL with connection pooling (PgBouncer)
- [ ] Configure Redis for analytics caching
- [ ] Train ML models on real data: `python spending_predictor.py --train`
- [ ] Set up daily Alembic migration runs in CI/CD
- [ ] Configure log aggregation (e.g., Datadog, Grafana Loki)

---

## 📦 Tech Stack Summary

| Layer      | Technology                              |
|------------|-----------------------------------------|
| Frontend   | React 18, Vite, TypeScript, Tailwind CSS |
| State      | Zustand (persist middleware)            |
| Charts     | Recharts                                |
| Backend    | FastAPI, Python 3.12, Uvicorn           |
| ORM        | SQLAlchemy 2.0 (async)                  |
| Database   | PostgreSQL 16                           |
| Cache      | Redis 7                                 |
| Auth       | JWT (python-jose) + bcrypt (passlib)    |
| ML         | scikit-learn, pandas, numpy             |
| Container  | Docker + Docker Compose                 |
| Migrations | Alembic                                 |

---

## 📄 License

MIT — free to use, modify, and deploy commercially.