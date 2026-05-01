#!python3
"""
Tests for GET /categories/{primary_category} and
GET /categories/{primary_category}/{detailed_category} endpoints.

Tests validate 404 on invalid categories and response shape on valid requests.
"""
import asyncio

import pandas as pd
import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock

from backend.api.categories.categories_router import (
    get_category_detail,
    get_subcategory_detail,
)
from backend.utils.analysis_utils import PrimaryCategories, DetailedCategories


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_mock_db(summary_rows=None, tx_rows=None):
    """Build a mock DatabaseSession for category detail endpoints."""
    db = MagicMock()

    db.summaries.fetch_all_items.return_value = summary_rows or []
    db.summaries.fetch_items_by_attribute.return_value = summary_rows or []

    tx_data = pd.DataFrame(tx_rows or [])
    mock_result = MagicMock()
    mock_result.data = tx_data
    db.transactions.query.return_value = mock_result
    db.transactions.return_columns = []

    db.budgets.fetch_item_by_id.return_value = None

    return db


def _make_summary_row(year=2025, month=1):
    row = MagicMock()
    row.year = year
    row.month = month
    row.budget_id = None
    for cat in PrimaryCategories:
        snake = cat.as_snake_case()
        setattr(row, f"sum_{snake}", 0.0)
        setattr(row, f"count_{snake}", 0)
        setattr(row, f"mean_{snake}", 0.0)
    for cat in DetailedCategories:
        snake = cat.as_snake_case()
        setattr(row, f"sum_{snake}", 0.0)
        setattr(row, f"count_{snake}", 0)
        setattr(row, f"mean_{snake}", 0.0)
    return row


# ─── GET /{primary_category} ──────────────────────────────────────────────────

class TestGetCategoryDetail:
    def test_404_for_invalid_primary_category(self):
        db = _make_mock_db()
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_category_detail("Not A Category", db))
        assert exc_info.value.status_code == 404

    def test_response_has_data_envelope(self):
        row = _make_summary_row()
        db = _make_mock_db(summary_rows=[row])
        result = asyncio.run(get_category_detail("Food & drink", db))
        assert "data" in result

    def test_response_shape(self):
        row = _make_summary_row()
        db = _make_mock_db(summary_rows=[row])
        result = asyncio.run(get_category_detail("Food & drink", db))
        data = result["data"]
        assert data["primaryCategory"] == "Food & drink"
        assert "spendOverTime" in data
        assert "subcategories" in data
        assert "currentMonthSubcategories" in data
        assert "currentMonthTotal" in data
        assert "currentMonthTxCount" in data
        assert "yearAvgSpend" in data
        assert "currentMonthTransactions" in data

    def test_spend_over_time_entry_per_summary_row(self):
        rows = [_make_summary_row(2025, m) for m in range(1, 4)]
        db = _make_mock_db(summary_rows=rows)
        result = asyncio.run(get_category_detail("Income", db))
        assert len(result["data"]["spendOverTime"]) == 3

    def test_spend_over_time_month_format(self):
        row = _make_summary_row(2025, 3)
        db = _make_mock_db(summary_rows=[row])
        result = asyncio.run(get_category_detail("Income", db))
        assert result["data"]["spendOverTime"][0]["month"] == "2025-03"

    def test_all_valid_primary_categories_accepted(self):
        db = _make_mock_db()
        for cat in PrimaryCategories:
            result = asyncio.run(get_category_detail(cat.value, db))
            assert "data" in result


# ─── GET /{primary_category}/{detailed_category} ──────────────────────────────

class TestGetSubcategoryDetail:
    def test_404_for_invalid_primary_category(self):
        db = _make_mock_db()
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_subcategory_detail("Not A Category", "Groceries", db))
        assert exc_info.value.status_code == 404

    def test_404_for_invalid_detailed_category(self):
        db = _make_mock_db()
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_subcategory_detail("Food & drink", "Not A Subcategory", db))
        assert exc_info.value.status_code == 404

    def test_response_has_data_envelope(self):
        db = _make_mock_db()
        result = asyncio.run(get_subcategory_detail("Food & drink", "Groceries", db))
        assert "data" in result

    def test_response_shape(self):
        db = _make_mock_db()
        result = asyncio.run(get_subcategory_detail("Food & drink", "Groceries", db))
        data = result["data"]
        assert data["primaryCategory"] == "Food & drink"
        assert data["detailedCategory"] == "Groceries"
        assert "transactionCount" in data
        assert "avgTransactionSize" in data
        assert "topVendors" in data
        assert "transactions" in data

    def test_transaction_count_from_query_results(self):
        tx_rows = [
            {"id": 1, "account_name": "Trader Joe's", "amount": -50.0,
             "authorized_date": "2025-01-10", "posted_date": "2025-01-11",
             "status": "posted", "description": "Groceries", "primary_category": "Food & drink",
             "detailed_category": "Groceries", "repayment": False, "exclude": False,
             "notes": None, "tags": None},
            {"id": 2, "account_name": "Whole Foods", "amount": -75.0,
             "authorized_date": "2025-01-12", "posted_date": "2025-01-13",
             "status": "posted", "description": "Groceries", "primary_category": "Food & drink",
             "detailed_category": "Groceries", "repayment": False, "exclude": False,
             "notes": None, "tags": None},
        ]
        db = _make_mock_db(tx_rows=tx_rows)
        result = asyncio.run(get_subcategory_detail("Food & drink", "Groceries", db))
        assert result["data"]["transactionCount"] == 2

    def test_top_vendors_aggregated_correctly(self):
        tx_rows = [
            {"id": 1, "account_name": "Trader Joe's", "amount": -50.0,
             "authorized_date": "2025-01-10", "posted_date": "2025-01-11",
             "status": "posted", "description": "", "primary_category": "Food & drink",
             "detailed_category": "Groceries", "repayment": False, "exclude": False,
             "notes": None, "tags": None},
            {"id": 2, "account_name": "Trader Joe's", "amount": -30.0,
             "authorized_date": "2025-01-15", "posted_date": "2025-01-16",
             "status": "posted", "description": "", "primary_category": "Food & drink",
             "detailed_category": "Groceries", "repayment": False, "exclude": False,
             "notes": None, "tags": None},
            {"id": 3, "account_name": "Whole Foods", "amount": -90.0,
             "authorized_date": "2025-01-20", "posted_date": "2025-01-21",
             "status": "posted", "description": "", "primary_category": "Food & drink",
             "detailed_category": "Groceries", "repayment": False, "exclude": False,
             "notes": None, "tags": None},
        ]
        db = _make_mock_db(tx_rows=tx_rows)
        result = asyncio.run(get_subcategory_detail("Food & drink", "Groceries", db))
        vendors = result["data"]["topVendors"]
        # Whole Foods has higher total ($90) than Trader Joe's ($80), should be first
        assert vendors[0]["name"] == "Whole Foods"
        assert vendors[1]["name"] == "Trader Joe's"
        assert vendors[1]["count"] == 2
