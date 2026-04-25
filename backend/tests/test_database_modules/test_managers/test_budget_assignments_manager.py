#!python3
"""
tests.test_database_modules.test_managers.test_budget_assignments_manager

Tests for BudgetAssignmentsManager — CRUD and get_effective_assignment logic.
"""
import pytest

from backend.tests.conftest import (
    clean_budget_assignments_database,
    test_budget_assignments_manager,
)


# ─── TestAddAssignment ────────────────────────────────────────────────────────

class TestAddAssignment:

    def test_add_assignment_stores_row(self, clean_budget_assignments_database):
        """add_item persists an assignment row with the correct field values."""
        clean_budget_assignments_database.add_item(
            budget_id=1, effective_from="2024-03", note="Q1 budget"
        )
        rows = clean_budget_assignments_database.get_all()
        assert len(rows) == 1
        row = rows[0]
        assert row.budget_id == 1
        assert row.effective_from == "2024-03"
        assert row.note == "Q1 budget"

    def test_note_is_optional(self, clean_budget_assignments_database):
        """add_item accepts a null note."""
        clean_budget_assignments_database.add_item(budget_id=2, effective_from="2024-06", note=None)
        row = clean_budget_assignments_database.get_all()[0]
        assert row.note is None


# ─── TestGetEffectiveAssignment ───────────────────────────────────────────────

class TestGetEffectiveAssignment:

    def test_exact_match(self, clean_budget_assignments_database):
        """Returns the assignment whose effective_from equals the query month exactly."""
        clean_budget_assignments_database.add_item(budget_id=1, effective_from="2024-03")
        result = clean_budget_assignments_database.get_effective_assignment("2024-03")
        assert result is not None
        assert result.effective_from == "2024-03"

    def test_earlier_assignment_covers_later_month(self, clean_budget_assignments_database):
        """Returns an assignment whose effective_from is before the query month."""
        clean_budget_assignments_database.add_item(budget_id=1, effective_from="2024-01")
        result = clean_budget_assignments_database.get_effective_assignment("2024-06")
        assert result is not None
        assert result.effective_from == "2024-01"

    def test_returns_none_when_no_eligible_assignment(self, clean_budget_assignments_database):
        """Returns None when all assignments start after the query month."""
        clean_budget_assignments_database.add_item(budget_id=1, effective_from="2025-01")
        result = clean_budget_assignments_database.get_effective_assignment("2024-06")
        assert result is None

    def test_returns_none_on_empty_table(self, clean_budget_assignments_database):
        """Returns None when the assignments table is empty."""
        result = clean_budget_assignments_database.get_effective_assignment("2024-06")
        assert result is None

    def test_returns_most_recent_of_multiple(self, clean_budget_assignments_database):
        """Returns the most recent eligible assignment when multiple qualify."""
        clean_budget_assignments_database.add_item(budget_id=1, effective_from="2024-01")
        clean_budget_assignments_database.add_item(budget_id=2, effective_from="2024-04")
        clean_budget_assignments_database.add_item(budget_id=3, effective_from="2025-01")

        # "2024-06" is after "2024-01" and "2024-04" but before "2025-01"
        result = clean_budget_assignments_database.get_effective_assignment("2024-06")
        assert result is not None
        assert result.budget_id == 2
        assert result.effective_from == "2024-04"
