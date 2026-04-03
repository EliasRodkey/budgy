#!python3
"""
backend.api.transactions.transactions_router

Contains FastAPI router for transaction-related endpoints, including fetching transactions with optional month/year filters and pagination.

Functions:
"""
# Third party imports
from fastapi import APIRouter, Depends

# Custom imports
from pleasant_database import DatabaseFile

# Local imports
from backend.api.transactions.transactions_models import Transaction, TransactionFilters
from backend.database_modules.managers.transaction_manager import TransactionsTableManager
from backend.utils.api_utils import RouterPrefixes
from backend.utils.file_utils import EDirectories

router = APIRouter(prefix=RouterPrefixes.TRANSACTIONS.value, tags=["Transactions"])


def get_db(db_file: DatabaseFile=DatabaseFile(EDirectories.DB_DIR, EDirectories.DB_FILENAME)):
    """
    Dependency function to get a database session for the transaction manager.
    """
    db = TransactionsTableManager()
    try:
        yield db
    finally:
        db.end_session()


@router.get("")
async def get_transactions(filters: TransactionFilters = Depends()):
    """"""
    tags_list = filters.tags.split(",") if filters.tags else None

