#!python3
"""
backend.database_modules.db_session

Provides DatabaseSession: a single context manager that owns one DatabaseFile
and all six manager instances built on top of it. Replaces the per-endpoint
manual manager construction and end_session() bookkeeping.

Usage (request dependency):
    def get_db():
        db_file = DatabaseFile(EDirectories.DB_FILENAME, EDirectories.DB_DIR)
        session = DatabaseSession(db_file)
        try:
            yield session
        finally:
            session.close()

Usage (background task):
    with DatabaseSession(db_file) as session:
        session.transactions.upload_csv(...)
"""
from pleasant_database import DatabaseFile

from backend.database_modules.managers.dirty_months_manager import DirtyMonthsManager
from backend.database_modules.managers.rules_manager import TransactionRulesManager
from backend.database_modules.managers.summary_manager import SummariesTableManager
from backend.database_modules.managers.transaction_manager import (
    TransactionsTableManager,
    UpdatesTableManager,
    UploadJobsManager,
)


class DatabaseSession:
    """Owns a single DatabaseFile and all manager instances built on it."""

    def __init__(self, db_file: DatabaseFile):
        # updates must be initialized before transactions (passed as constructor arg)
        self.updates = UpdatesTableManager(db_file)
        self.transactions = TransactionsTableManager(db_file, self.updates)
        self.rules = TransactionRulesManager(db_file)
        self.dirty_months = DirtyMonthsManager(db_file)
        self.summaries = SummariesTableManager(db_file)
        self.jobs = UploadJobsManager(db_file)

    def close(self) -> None:
        for mgr in [
            self.transactions,
            self.updates,
            self.rules,
            self.dirty_months,
            self.summaries,
            self.jobs,
        ]:
            mgr.end_session()

    def __enter__(self) -> "DatabaseSession":
        return self

    def __exit__(self, *_) -> None:
        self.close()
