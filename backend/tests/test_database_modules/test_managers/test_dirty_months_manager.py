#!python3
"""
tests.test_database_modules.test_managers.test_dirty_months_manager.py

Tests for backend.database_modules.managers.dirty_months_manager.py — DirtyMonthsManager.

DirtyMonthsManager is a queue: mark_dirty inserts or updates a row, get_all_dirty
returns all queued (month, year) pairs, any_dirty is a quick boolean check, and clear
removes a specific row after recompute.
"""
# Third party imports
import pytest

# Local imports
from backend.tests.conftest import clean_dirty_months_database


# ─── TestMarkDirty ────────────────────────────────────────────────────────────

class TestMarkDirty:

    def test_inserts_a_new_record(self, clean_dirty_months_database):
        """mark_dirty persists a (month, year) record so it appears in get_all_dirty."""
        mgr = clean_dirty_months_database
        mgr.mark_dirty(4, 2026)
        assert (4, 2026) in mgr.get_all_dirty()

    def test_idempotent_no_duplicate(self, clean_dirty_months_database):
        """Calling mark_dirty twice for the same month/year does not create two rows."""
        mgr = clean_dirty_months_database
        mgr.mark_dirty(4, 2026)
        mgr.mark_dirty(4, 2026)
        pairs = mgr.get_all_dirty()
        assert pairs.count((4, 2026)) == 1

    def test_multiple_distinct_months_are_independent(self, clean_dirty_months_database):
        """mark_dirty for different month/year pairs each produce their own row."""
        mgr = clean_dirty_months_database
        mgr.mark_dirty(3, 2026)
        mgr.mark_dirty(4, 2026)
        pairs = mgr.get_all_dirty()
        assert (3, 2026) in pairs
        assert (4, 2026) in pairs
        assert len(pairs) == 2

    def test_different_years_are_independent(self, clean_dirty_months_database):
        """Same month in different years are treated as distinct dirty-month records."""
        mgr = clean_dirty_months_database
        mgr.mark_dirty(1, 2025)
        mgr.mark_dirty(1, 2026)
        pairs = mgr.get_all_dirty()
        assert (1, 2025) in pairs
        assert (1, 2026) in pairs
        assert len(pairs) == 2


# ─── TestGetAllDirty ──────────────────────────────────────────────────────────

class TestGetAllDirty:

    def test_returns_empty_list_when_queue_is_empty(self, clean_dirty_months_database):
        """get_all_dirty returns an empty list when no months have been marked."""
        mgr = clean_dirty_months_database
        assert mgr.get_all_dirty() == []

    def test_returns_list_of_tuples(self, clean_dirty_months_database):
        """get_all_dirty returns a list of (month, year) int tuples."""
        mgr = clean_dirty_months_database
        mgr.mark_dirty(4, 2026)
        pairs = mgr.get_all_dirty()
        assert isinstance(pairs, list)
        assert len(pairs) == 1
        month, year = pairs[0]
        assert month == 4
        assert year == 2026

    def test_returns_all_queued_months(self, clean_dirty_months_database):
        """get_all_dirty includes every mark_dirty call made so far."""
        mgr = clean_dirty_months_database
        expected = {(1, 2025), (6, 2025), (12, 2025)}
        for month, year in expected:
            mgr.mark_dirty(month, year)
        assert set(mgr.get_all_dirty()) == expected


# ─── TestAnyDirty ─────────────────────────────────────────────────────────────

class TestAnyDirty:

    def test_returns_false_when_empty(self, clean_dirty_months_database):
        """any_dirty returns False when the queue is empty."""
        mgr = clean_dirty_months_database
        assert mgr.any_dirty() is False

    def test_returns_true_after_mark_dirty(self, clean_dirty_months_database):
        """any_dirty returns True as soon as one month is marked."""
        mgr = clean_dirty_months_database
        mgr.mark_dirty(4, 2026)
        assert mgr.any_dirty() is True

    def test_returns_false_after_all_cleared(self, clean_dirty_months_database):
        """any_dirty returns False once all dirty months have been cleared."""
        mgr = clean_dirty_months_database
        mgr.mark_dirty(4, 2026)
        mgr.clear(4, 2026)
        assert mgr.any_dirty() is False


# ─── TestClear ────────────────────────────────────────────────────────────────

class TestClear:

    def test_removes_the_specified_month(self, clean_dirty_months_database):
        """clear removes only the given (month, year) from the queue."""
        mgr = clean_dirty_months_database
        mgr.mark_dirty(4, 2026)
        mgr.clear(4, 2026)
        assert (4, 2026) not in mgr.get_all_dirty()

    def test_does_not_remove_other_months(self, clean_dirty_months_database):
        """clear leaves all other dirty months untouched."""
        mgr = clean_dirty_months_database
        mgr.mark_dirty(3, 2026)
        mgr.mark_dirty(4, 2026)
        mgr.clear(3, 2026)
        pairs = mgr.get_all_dirty()
        assert (3, 2026) not in pairs
        assert (4, 2026) in pairs

    def test_clear_nonexistent_month_does_not_raise(self, clean_dirty_months_database):
        """clear on a month that was never marked does not raise."""
        mgr = clean_dirty_months_database
        mgr.clear(1, 2000)  # should not raise
