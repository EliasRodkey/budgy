#!python3
"""
Tests for DatabaseSession context manager.

Verifies construction, close(), and context-manager __enter__/__exit__ behaviour.
Uses the shared test DatabaseFile from conftest.py to verify real construction,
and unittest.mock.patch to verify that close() calls end_session() on all managers.
"""
from unittest.mock import MagicMock, patch

import pytest

from backend.database_modules.db_session import DatabaseSession
from backend.tests.conftest import test_db_file


class TestDatabaseSessionConstruction:
    def test_constructs_without_error(self):
        session = DatabaseSession(test_db_file)
        session.close()

    def test_has_all_managers(self):
        session = DatabaseSession(test_db_file)
        try:
            assert hasattr(session, "transactions")
            assert hasattr(session, "updates")
            assert hasattr(session, "rules")
            assert hasattr(session, "dirty_months")
            assert hasattr(session, "summaries")
            assert hasattr(session, "jobs")
        finally:
            session.close()

    def test_updates_is_transactions_dependency(self):
        """TransactionsTableManager must receive the same UpdatesTableManager instance."""
        session = DatabaseSession(test_db_file)
        try:
            # TransactionsTableManager stores its updates_manager as .updates_manager
            assert session.transactions.updates_manager is session.updates
        finally:
            session.close()


class TestDatabaseSessionClose:
    def test_close_calls_end_session_on_all_managers(self):
        session = DatabaseSession(test_db_file)
        managers = [
            session.transactions,
            session.updates,
            session.rules,
            session.dirty_months,
            session.summaries,
            session.jobs,
        ]
        for mgr in managers:
            mgr.end_session = MagicMock()

        session.close()

        for mgr in managers:
            mgr.end_session.assert_called_once()


class TestDatabaseSessionContextManager:
    def test_context_manager_returns_self(self):
        session = DatabaseSession(test_db_file)
        with session as s:
            assert s is session

    def test_context_manager_calls_close_on_normal_exit(self):
        session = DatabaseSession(test_db_file)
        session.close = MagicMock()
        with session:
            pass
        session.close.assert_called_once()

    def test_context_manager_calls_close_on_exception(self):
        session = DatabaseSession(test_db_file)
        session.close = MagicMock()
        with pytest.raises(RuntimeError):
            with session:
                raise RuntimeError("test error")
        session.close.assert_called_once()
