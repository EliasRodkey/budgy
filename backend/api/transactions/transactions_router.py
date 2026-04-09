#!python3
"""
backend.api.transactions.transactions_router

Contains FastAPI router for transaction-related endpoints, including fetching transactions with optional month/year filters and pagination.

Functions:
"""
# Third party imports
from fastapi import APIRouter, Depends

# Custom imports
from pleasant_database import DatabaseFile, DatabaseManager

# Local imports
from backend.api.transactions.transactions_models import Transaction, TransactionFilters, PaginatedTransactions
from backend.database_modules.managers.transaction_manager import TransactionsTableManager
from backend.utils.api_utils import RouterPrefixes
from backend.utils.file_utils import EDirectories

router = APIRouter(prefix=RouterPrefixes.TRANSACTIONS.value, tags=["Transactions"])


def get_db():
    """
    Dependency function to get a database session for the transaction manager.
    Attached to live database file.
    """
    db = TransactionsTableManager(DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR))
    try:
        yield db
    finally:
        db.end_session()


@router.get("", tags=["Transactions"], response_model=PaginatedTransactions)
async def get_transaction_pages(
    filters: TransactionFilters = Depends(), 
    db: DatabaseManager = Depends(get_db)
) -> list[Transaction]:
    """
    API endpoint to fetch transactions with optional filters and pagination.
    
    Args:
        filters (TransactionFilters): Query parameters for filtering and pagination.
        db (DatabaseManager): Database session dependency.

    Returns:
        List of transactions matching the filters.
    """
    tags_list = filters.tags.split(",") if filters.tags else None

    # TODO: Implement all of this logic in the manager, too much thinking here.
    # Should just be able to pass the parameters to the manager. May want to think about additions to db_manager too.
    # TODO: Add limit, offset, and sorting logic in manager query builder as well.
    filter_dict = {
        "search": ("==", filters.search), # TODO: Implement search logic in manager to search across description, account name, and maybe categories.
        "primary_category": ("==", filters.primary_category),
        "detailed_category": ("==", filters.detailed_category),
        "tags": ("in", tags_list),
        "exclude": ("==", filters.show_excluded),
        "authorized_date": ("between", (filters.date_from, filters.date_to)),
        # "sort_by": ("==", filters.sort_by),
        # "sort_order": ("==", filters.sort_order),
        # "page": ("==", filters.page),
        # "page_size": ("==", filters.page_size)
    }
    total_count = len(filter_dict)

    transactions = db.filter_items(filter_dict, use_or=True)

    return {
        "data": transactions,
        "total": total_count,
        "page": filters.page,
        "page_size": filters.page_size
    }

