#!python3
"""
backend.main
"""
# Third party imports
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Local imports
from backend.api.transactions.transactions_router import router as transactions_router
from backend.api.summaries.summaries_router import router as summaries_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transactions_router)
app.include_router(summaries_router)