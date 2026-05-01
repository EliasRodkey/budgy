#!python3
"""
backend.main
"""
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