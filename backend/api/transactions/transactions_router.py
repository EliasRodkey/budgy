#!python3
"""
backend.api.transactions.transactions_router

Contains FastAPI router for transaction-related endpoints, including fetching transactions with optional month/year filters and pagination.

Functions:
"""
# Standard library imports
from datetime import datetime

# Third party imports
from fastapi import APIRouter, Depends

# Custom imports
from pleasant_database import DatabaseFile, DatabaseManager

# Local imports
from backend.api.transactions.transactions_models import Transaction, TransactionFilters, TransactionsPage
from backend.database_modules.managers.transaction_manager import TransactionsTableManager
from backend.database_modules.models.transactions import TransactionsTable
from backend.utils.analysis_utils import PrimaryCategories, DetailedCategories
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


@router.get("", tags=["Transactions"], response_model=TransactionsPage)
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
    # Build database filters for query (and logic filters only)
    db_filters = {}
    db_filters[TransactionsTable.exclude.name] = ("==", filters.show_excluded)
    if filters.primary_category in PrimaryCategories.__members__:
        db_filters[TransactionsTable.primary_category.name] = ("==", filters.primary_category)
    
    if filters.detailed_category in DetailedCategories.__members__:
        db_filters[TransactionsTable.detailed_category.name] = ("==", filters.detailed_category)
    
    if filters.date_from or filters.date_to:
        date_from = filters.date_from or "1900-01-01"
        date_to = filters.date_to or datetime.now().strftime("%Y-%m-%d")
        db_filters[TransactionsTable.posted_date.name] = ("between", (datetime.strptime(date_from, "%Y-%m-%d"), datetime.strptime(date_to, "%Y-%m-%d")))

    # Query returns a df object, wil have to pply additional or filters (tags_list) to the dataframe, then convert to return data
    result = db.query(
        columns = db.return_columns,
        filters = db_filters,
        order_by = filters.sort_by,
        ascending = (filters.sort_order != "desc"),
        limit = filters.page_size,
        offset = (filters.page - 1) * filters.page_size,
        search = filters.search,
        search_columns = db.search_columns
    )

    # Extract resulting dataframe
    transactions_df = result.data

    # Seperate tags into distinct values if provided and combine filtering with a mask.
    if filters.tags:
        tags_list = filters.tags.split(",") if filters.tags else None
        masks = []
        for tag in tags_list:
            masks.append(transactions_df.tags.str.contains(tag.strip(), na=False))
        
        combined_mask = masks[0]
        for mask in masks[1:]:
            combined_mask = combined_mask | mask
        
        transactions_df = transactions_df[combined_mask]

    transactions = transactions_df.to_dict(orient="records")

    return {
        "data": transactions,
        "total": result.total_count,
        "page": filters.page,
        "page_size": len(transactions),
        "has_next_page": result.has_next
    }

