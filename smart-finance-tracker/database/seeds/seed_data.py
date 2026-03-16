"""
database/seeds/seed_data.py
Populate the database with realistic sample data for development/demo
Run: python seed_data.py
"""
import asyncio
import random
from datetime import date, timedelta

import asyncpg

DB_URL = "postgresql://postgres:password@localhost:5432/finance_db"

CATEGORIES = [
    ("Food & Dining",    "🍔", "#f59e0b", "expense"),
    ("Transportation",   "🚗", "#3b82f6", "expense"),
    ("Shopping",         "🛍️", "#ec4899", "expense"),
    ("Bills & Utilities","⚡", "#8b5cf6", "expense"),
    ("Entertainment",    "🎬", "#f97316", "expense"),
    ("Health & Fitness", "💊", "#10b981", "expense"),
    ("Travel",           "✈️", "#06b6d4", "expense"),
    ("Education",        "📚", "#84cc16", "expense"),
    ("Salary",           "💼", "#22c55e", "income"),
    ("Freelance",        "💻", "#a3e635", "income"),
]

MERCHANTS = {
    "Food & Dining":    ["McDonald's", "Starbucks", "Domino's", "Swiggy", "Zomato"],
    "Transportation":   ["Uber", "Ola", "Metro Card", "Petrol Station", "Bus Pass"],
    "Shopping":         ["Amazon", "Flipkart", "H&M", "Zara", "IKEA"],
    "Bills & Utilities":["Electricity Board", "Internet Provider", "Gas Company", "Water Utility"],
    "Entertainment":    ["Netflix", "Spotify", "BookMyShow", "Steam"],
    "Health & Fitness": ["Apollo Pharmacy", "Gold's Gym", "Dr. Consultation", "Medplus"],
    "Travel":           ["MakeMyTrip", "IRCTC", "Hotel Booking", "Airbnb"],
    "Education":        ["Udemy", "Coursera", "Book Store", "Stationery"],
    "Salary":           ["Employer Corp"],
    "Freelance":        ["Client Payment", "Upwork", "Toptal"],
}


async def seed():
    conn = await asyncpg.connect(DB_URL)

    # Create test user
    user_id = await conn.fetchval("""
        INSERT INTO users (email, hashed_password, full_name, currency, monthly_income)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
        RETURNING id
    """, "demo@financeai.com",
        "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMaWkal2t89tFYF0IaTUL0YXMO",  # password: Demo@1234
        "Demo User", "USD", 8000.0)

    print(f"User created: {user_id}")

    # Create categories
    cat_ids = {}
    for name, icon, color, ctype in CATEGORIES:
        cat_id = await conn.fetchval("""
            INSERT INTO categories (user_id, name, icon, color, type)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT DO NOTHING
            RETURNING id
        """, user_id, name, icon, color, ctype)
        if cat_id:
            cat_ids[name] = cat_id

    print(f"Categories: {len(cat_ids)}")

    # Re-fetch if already existed
    rows = await conn.fetch("SELECT id, name FROM categories WHERE user_id=$1", user_id)
    for r in rows:
        cat_ids[r["name"]] = r["id"]

    # Generate 6 months of transactions
    tx_count = 0
    today = date.today()
    for month_offset in range(6):
        tx_date = today.replace(day=1) - timedelta(days=month_offset * 30)

        # Monthly salary
        sal_id = cat_ids.get("Salary")
        if sal_id:
            await conn.execute("""
                INSERT INTO transactions (user_id, category_id, amount, type, description, merchant, date)
                VALUES ($1,$2,$3,$4,$5,$6,$7)
            """, user_id, sal_id, round(random.uniform(7500, 8500), 2),
                "income", "Monthly Salary", "Employer Corp",
                tx_date.replace(day=1))
            tx_count += 1

        # Occasional freelance
        if random.random() > 0.5:
            fl_id = cat_ids.get("Freelance")
            if fl_id:
                await conn.execute("""
                    INSERT INTO transactions (user_id, category_id, amount, type, description, merchant, date)
                    VALUES ($1,$2,$3,$4,$5,$6,$7)
                """, user_id, fl_id, round(random.uniform(500, 2000), 2),
                    "income", "Freelance Project", "Client Payment",
                    tx_date.replace(day=random.randint(5, 25)))
                tx_count += 1

        # Expense transactions — 15–25 per month
        expense_cats = [c for c in CATEGORIES if c[3] == "expense"]
        for _ in range(random.randint(15, 25)):
            cat = random.choice(expense_cats)
            cat_name = cat[0]
            cat_id   = cat_ids.get(cat_name)
            if not cat_id:
                continue
            merchant = random.choice(MERCHANTS.get(cat_name, ["Unknown"]))
            amt_ranges = {
                "Food & Dining": (20, 150), "Transportation": (10, 100),
                "Shopping": (50, 500), "Bills & Utilities": (50, 300),
                "Entertainment": (10, 100), "Health & Fitness": (30, 200),
                "Travel": (100, 800), "Education": (20, 200),
            }
            lo, hi = amt_ranges.get(cat_name, (20, 200))
            amount   = round(random.uniform(lo, hi), 2)
            day      = random.randint(1, 28)
            tx_day   = tx_date.replace(day=day)

            # Inject a few anomalies
            is_anomaly = random.random() < 0.05
            if is_anomaly:
                amount = round(amount * random.uniform(4, 8), 2)

            await conn.execute("""
                INSERT INTO transactions
                    (user_id, category_id, amount, type, description, merchant, date, is_anomaly)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
            """, user_id, cat_id, amount, "expense",
                f"{cat_name} purchase", merchant, tx_day, is_anomaly)
            tx_count += 1

    print(f"Transactions seeded: {tx_count}")

    # Budgets for current month
    budget_defaults = {
        "Food & Dining": 600, "Transportation": 200, "Shopping": 400,
        "Bills & Utilities": 350, "Entertainment": 150, "Health & Fitness": 200,
    }
    for cat_name, budget_amt in budget_defaults.items():
        cat_id = cat_ids.get(cat_name)
        if cat_id:
            await conn.execute("""
                INSERT INTO budgets (user_id, category_id, amount, period, month, year)
                VALUES ($1,$2,$3,$4,$5,$6)
                ON CONFLICT DO NOTHING
            """, user_id, cat_id, budget_amt, "monthly",
                today.month, today.year)

    print("Budgets seeded")
    await conn.close()
    print("\n✅ Seed complete!")
    print("   Email:    demo@financeai.com")
    print("   Password: Demo@1234")


if __name__ == "__main__":
    asyncio.run(seed())
