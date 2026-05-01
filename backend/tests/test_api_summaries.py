#!python3
"""
Tests for the GET /summaries/{month_str} endpoint logic.

Tests focus on the _build_monthly_summary helper (pure transformation logic)
and the HTTP-level validation (422 on bad format, 404 on missing row).
"""
import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock, patch

from backend.api.summaries.summaries_router import (
    _build_monthly_summary,
    get_monthly_summary,
    MonthlySummaryResponse,
    CategorySpendResponse,
)
from backend.utils.analysis_utils import PrimaryCategories


# ─── Fixtures ─────────────────────────────────────────────────────────────────

def _make_summary_row(budget_id=None):
    """Build a minimal mock summary ORM row with all required column attributes."""
    row = MagicMock()
    row.budget_id = budget_id
    for cat in PrimaryCategories:
        snake = cat.as_snake_case()
        setattr(row, f"sum_{snake}", 0.0)
        setattr(row, f"count_{snake}", 0)
        setattr(row, f"mean_{snake}", 0.0)
    # Add some non-zero values
    row.sum_income = 2000.0
    row.count_income = 2
    row.mean_income = 1000.0
    row.sum_food_and_drink = 350.0
    row.count_food_and_drink = 5
    row.mean_food_and_drink = 70.0
    return row


@pytest.fixture
def summary_row():
    return _make_summary_row()


@pytest.fixture
def mock_session(summary_row):
    session = MagicMock()
    session.budgets.fetch_item_by_id.return_value = None
    return session


# ─── _build_monthly_summary ───────────────────────────────────────────────────

class TestBuildMonthlySummary:
    def test_returns_monthly_summary_response(self, summary_row, mock_session):
        result = _build_monthly_summary(summary_row, "2025-01", mock_session)
        assert isinstance(result, MonthlySummaryResponse)

    def test_month_field_preserved(self, summary_row, mock_session):
        result = _build_monthly_summary(summary_row, "2025-03", mock_session)
        assert result.month == "2025-03"

    def test_by_category_has_16_entries(self, summary_row, mock_session):
        result = _build_monthly_summary(summary_row, "2025-01", mock_session)
        assert len(result.by_category) == 16

    def test_all_primary_categories_present(self, summary_row, mock_session):
        result = _build_monthly_summary(summary_row, "2025-01", mock_session)
        names = {c.category_name for c in result.by_category}
        expected = {cat.value for cat in PrimaryCategories}
        assert names == expected

    def test_income_total_correct(self, summary_row, mock_session):
        result = _build_monthly_summary(summary_row, "2025-01", mock_session)
        assert result.total_income == 2000.0

    def test_net_equals_income_minus_expenses(self, summary_row, mock_session):
        result = _build_monthly_summary(summary_row, "2025-01", mock_session)
        assert abs(result.net - (result.total_income - result.total_expenses)) < 0.001

    def test_food_category_amount_correct(self, summary_row, mock_session):
        result = _build_monthly_summary(summary_row, "2025-01", mock_session)
        food = next(c for c in result.by_category if c.category_name == "Food & drink")
        assert food.amount == 350.0
        assert food.transaction_count == 5

    def test_monthly_limit_none_without_budget(self, summary_row, mock_session):
        result = _build_monthly_summary(summary_row, "2025-01", mock_session)
        for cat in result.by_category:
            assert cat.monthly_limit is None
            assert cat.percent_of_limit is None
            assert cat.is_over_budget is False

    def test_budget_limits_applied_when_budget_present(self, mock_session):
        row = _make_summary_row(budget_id=1)
        budget_row = MagicMock()
        for cat in PrimaryCategories:
            setattr(budget_row, cat.as_snake_case(), 500.0)
        mock_session.budgets.fetch_item_by_id.return_value = budget_row

        result = _build_monthly_summary(row, "2025-01", mock_session)
        food = next(c for c in result.by_category if c.category_name == "Food & drink")
        assert food.monthly_limit == 500.0
        assert food.percent_of_limit == pytest.approx(70.0, rel=0.01)
        assert food.is_over_budget is False

    def test_is_over_budget_when_exceeds_limit(self, mock_session):
        row = _make_summary_row(budget_id=1)
        row.sum_food_and_drink = 600.0
        row.count_food_and_drink = 8
        budget_row = MagicMock()
        for cat in PrimaryCategories:
            setattr(budget_row, cat.as_snake_case(), 500.0)
        mock_session.budgets.fetch_item_by_id.return_value = budget_row

        result = _build_monthly_summary(row, "2025-01", mock_session)
        food = next(c for c in result.by_category if c.category_name == "Food & drink")
        assert food.is_over_budget is True


# ─── HTTP endpoint validation ─────────────────────────────────────────────────

class TestGetMonthlySummaryEndpoint:
    def test_422_on_bad_month_format(self):
        import asyncio
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_monthly_summary("bad-format"))
        assert exc_info.value.status_code == 422

    def test_422_on_missing_day(self):
        import asyncio
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_monthly_summary("2025-01-15"))
        assert exc_info.value.status_code == 422

    def test_404_when_no_summary_row(self):
        import asyncio
        with patch("backend.api.summaries.summaries_router.DatabaseSession") as MockSession:
            mock_ctx = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=MagicMock(
                summaries=MagicMock(fetch_items_by_attribute=MagicMock(return_value=[]))
            ))
            mock_ctx.__exit__ = MagicMock(return_value=False)
            MockSession.return_value = mock_ctx

            with pytest.raises(HTTPException) as exc_info:
                asyncio.run(get_monthly_summary("2025-01"))
            assert exc_info.value.status_code == 404

    def test_returns_data_envelope(self):
        import asyncio
        row = _make_summary_row()
        with patch("backend.api.summaries.summaries_router.DatabaseSession") as MockSession:
            mock_session_obj = MagicMock()
            mock_session_obj.summaries.fetch_items_by_attribute.return_value = [row]
            mock_session_obj.budgets.fetch_item_by_id.return_value = None
            mock_ctx = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=mock_session_obj)
            mock_ctx.__exit__ = MagicMock(return_value=False)
            MockSession.return_value = mock_ctx

            result = asyncio.run(get_monthly_summary("2025-01"))
        assert "data" in result
        assert result["data"]["month"] == "2025-01"
        assert "byCategory" in result["data"]
