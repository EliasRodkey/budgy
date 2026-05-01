#!python3
"""
backend.main
"""
from dotenv import load_dotenv
load_dotenv()

import sqlite3
import os

def _migrate_db() -> None:
    db_path = os.path.join(os.getcwd(), "data", "databases", "budgy_financial_transaction.db")
    if not os.path.exists(db_path):
        return
    conn = sqlite3.connect(db_path)
    try:
        existing = {row[1] for row in conn.execute("PRAGMA table_info(upload_jobs)")}
        for col in ("rules_applied_from_cache", "new_rules_saved"):
            if col not in existing:
                conn.execute(f"ALTER TABLE upload_jobs ADD COLUMN {col} INTEGER")
        conn.commit()
    finally:
        conn.close()

_migrate_db()

# Third party imports
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Local imports
from backend.api.ai.ai_router import router as ai_router
from backend.api.analytics.analytics_router import router as analytics_router
from backend.api.budgets.budgets_router import router as budgets_router
from backend.api.categories.categories_router import router as categories_router
from backend.api.summaries.summaries_router import router as summaries_router
from backend.api.transactions.transactions_router import router as transactions_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_router)
app.include_router(categories_router)
app.include_router(transactions_router)
app.include_router(summaries_router)
app.include_router(analytics_router)
app.include_router(budgets_router)