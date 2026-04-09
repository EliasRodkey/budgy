#!python3
"""
backend.main
"""
# Third party imports
from fastapi import FastAPI

# Local imports
from backend.api.transactions.transactions_router import router as transactions_router

app = FastAPI()

app.include_router(transactions_router)