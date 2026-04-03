#!python3
"""
Shared pytest fixtures and test database setup for test_utils.

Provides:
    - Test database path constants (TEST_CSV_DIR, TEST_DB_DIR, etc.)
    - Test manager instances (test_transaction_manager, test_updates_manager,
      test_budgets_manager, test_summaries_manager)
    - clean_updates_database fixture: populates the updates table with sample data, tears down after each test
    - clean_transactions_database fixture: yields an empty transactions table, tears down after each test
    - full_transactions_database fixture: populates the transactions table with data from a test CSV, tears down after each test
    - clean_budgets_database fixture: yields an empty budgets table, tears down after each test
    - clean_summaries_database fixture: yields an empty summaries table (with budget row), tears down after each test
"""
# Standard library imports
import os
from datetime import datetime

# Third party imports
import pytest

# Custom imports
from pleasant_database import DatabaseFile
from pleasant_loggers import configure_logging, LoggingMode

# Local imports
from backend.database_modules.managers.transaction_manager import TransactionsTableManager, UpdatesTableManager
from backend.database_modules.managers.budget_manager import BudgetsTableManager
from backend.database_modules.managers.summary_manager import SummariesTableManager
from backend.database_modules.models.common import TableStatus
from backend.utils.file_utils import EDirectories


@pytest.fixture(scope="session", autouse=True)
def configure_test_logging():
    configure_logging(
        log_directory=EDirectories.LOG_DIR,
        mode=LoggingMode.DAILY_DIRECTORY, # TODO: Seeing an issue with the log creation, Getting the single file per run instead of the daily directory! and no JSON
        )


TEST_CSV_DIR = os.path.join(os.getcwd(), "backend", "tests", "test_csv_download_files")
TEST_DB_DIR = os.path.join(os.getcwd(), "backend", "tests", "test_databases")
TEST_DB_FILENAME = "test_database.db"
TEST_DB_FILEPATH = os.path.join(TEST_DB_DIR, TEST_DB_FILENAME)

test_db_file = DatabaseFile(TEST_DB_FILEPATH, TEST_DB_DIR)
test_updates_manager = UpdatesTableManager(test_db_file)
test_transaction_manager = TransactionsTableManager(test_db_file, test_updates_manager)
test_budgets_manager = BudgetsTableManager(test_db_file)
test_summaries_manager = SummariesTableManager(test_db_file)

TEST_FULL_TRANSACTIONS_CSV = os.path.join(TEST_CSV_DIR, "SoFi-Relay-All-Transactions_2025-12-31.csv")

update_items = [
    {
        "timestamp": datetime(2024, 1, 1),
        "filepath": os.path.join(TEST_CSV_DIR, "TEST_UPDATE.csv"),
        "status": TableStatus.COMPLETE
    },
    {
        "timestamp": datetime(2024, 1, 2),
        "filepath": os.path.join(TEST_CSV_DIR, "transactions_1.csv"),
        "status": TableStatus.COMPLETE
    },
    {
        "timestamp": datetime(2024, 1, 3),
        "filepath": os.path.join(TEST_CSV_DIR, "transactions_2.csv"),
        "status": TableStatus.INCOMPLETE
    },
    {
        "timestamp": datetime(2024, 1, 5),
        "filepath": os.path.join(TEST_CSV_DIR, "hsbifunsdovns.csv"),
        "status": "Error - hdchiboenc"
    }
]


@pytest.fixture()
def clean_updates_database():
    """Fixture to populate and clean the updates table before and after each test."""
    db_manager = test_updates_manager

    try:
        db_manager.add_multiple_items(update_items)
        yield db_manager

    except Exception:
        db_manager.session.rollback()
        raise

    finally:
        db_manager.clear_table()
        db_manager.end_session()


@pytest.fixture()
def clean_transactions_database():
    """Fixture to provide and clean the transactions table before and after each test."""
    db_manager = test_transaction_manager

    try:
        yield db_manager

    except Exception:
        db_manager.session.rollback()
        raise

    finally:
        db_manager.clear_table()
        db_manager.end_session()


@pytest.fixture()
def full_transactions_database():
    """Fixture to provide and loaded transactions table before and after each test."""
    db_manager = test_transaction_manager

    try:
        # Add transactions from the loaded csv to the test db
        db_manager.upload_csv(TEST_FULL_TRANSACTIONS_CSV)
        yield db_manager

    except Exception:
        db_manager.session.rollback()
        raise

    finally:
        db_manager.updates_manager.clear_table()
        db_manager.updates_manager.end_session()
        db_manager.clear_table()
        db_manager.end_session()


@pytest.fixture()
def clean_budgets_database():
    """Fixture to provide and clean the budgets table before and after each test."""
    db_manager = test_budgets_manager

    try:
        yield db_manager

    except Exception:
        db_manager.session.rollback()
        raise

    finally:
        db_manager.clear_table()
        db_manager.end_session()


@pytest.fixture()
def clean_summaries_database(clean_budgets_database):
    """Fixture to provide and clean the summaries table before and after each test.
    Depends on clean_budgets_database since SummariesTable has a FK to budgets.
    """
    db_manager = test_summaries_manager

    try:
        yield db_manager, clean_budgets_database

    except Exception:
        db_manager.session.rollback()
        raise

    finally:
        db_manager.clear_table()
        db_manager.end_session()


@pytest.fixture()
def full_summaries_database(clean_budgets_database, full_transactions_database):
    """Fixture to provide and clean the summaries table before and after each test.
    Depends on clean_budgets_database since SummariesTable has a FK to budgets.
    """
    db_manager = test_summaries_manager
    for month, year in full_transactions_database.retrieve_month_year_pairs():
        summary = full_transactions_database.generate_monthly_summary(month, year)
        db_manager.upload_monthly_summary(month, year, summary, budget_id=1)

    try:
        yield db_manager, clean_budgets_database

    except Exception:
        db_manager.session.rollback()
        raise

    finally:
        db_manager.clear_table()
        db_manager.end_session()
