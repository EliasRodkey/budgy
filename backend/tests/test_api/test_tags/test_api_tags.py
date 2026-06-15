#!python3
"""
Tests for GET /tags and GET /tags/{tag_name} endpoints.

Tags are stored as a comma-separated string column on the transactions table, so
all aggregation is computed on-the-fly from queried transaction rows. These tests
mock the DatabaseSession to control the rows returned by db.transactions.query.
"""
import asyncio
from unittest.mock import MagicMock

import pandas as pd
import pytest
from fastapi import HTTPException

from backend.api.tags.tags_router import get_tag_detail, get_tags_overview
from backend.database_modules.models.transactions import TransactionsTable


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _row(
    id_, amount, primary_category, tags, authorized_date="2025-01-10",
    description="Test transaction", account_name="Chase", status="posted",
    detailed_category="Groceries", repayment=False, exclude=False, notes=None,
    posted_date=None,
):
    return {
        TransactionsTable.id.name: id_,
        TransactionsTable.authorized_date.name: authorized_date,
        TransactionsTable.posted_date.name: posted_date or authorized_date,
        TransactionsTable.status.name: status,
        TransactionsTable.account_name.name: account_name,
        TransactionsTable.description.name: description,
        TransactionsTable.primary_category.name: primary_category,
        TransactionsTable.detailed_category.name: detailed_category,
        TransactionsTable.amount.name: amount,
        TransactionsTable.repayment.name: repayment,
        TransactionsTable.exclude.name: exclude,
        TransactionsTable.notes.name: notes,
        TransactionsTable.tags.name: tags,
    }


def _make_mock_db(tx_rows=None):
    db = MagicMock()
    mock_result = MagicMock()
    mock_result.data = pd.DataFrame(tx_rows or [])
    db.transactions.query.return_value = mock_result
    db.transactions.return_columns = []
    return db


# ─── GET /tags ────────────────────────────────────────────────────────────────

class TestGetTagsOverview:
    def test_empty_transactions_returns_empty_list(self):
        db = _make_mock_db()
        result = asyncio.run(get_tags_overview(db=db))
        assert result == {"data": []}

    def test_no_tags_returns_empty_list(self):
        rows = [_row(1, -50.0, "Food & drink", tags=None)]
        db = _make_mock_db(rows)
        result = asyncio.run(get_tags_overview(db=db))
        assert result == {"data": []}

    def test_single_tag_totals(self):
        rows = [
            _row(1, -50.0, "Food & drink", tags="trip"),
            _row(2, -30.0, "Travel", tags="trip"),
        ]
        db = _make_mock_db(rows)
        result = asyncio.run(get_tags_overview(db=db))
        assert result["data"] == [
            {"tagName": "trip", "totalSpend": 80.0, "transactionCount": 2}
        ]

    def test_multiple_tags_on_one_transaction_each_counted(self):
        rows = [_row(1, -50.0, "Food & drink", tags="trip, dinner")]
        db = _make_mock_db(rows)
        result = asyncio.run(get_tags_overview(db=db))
        by_tag = {d["tagName"]: d for d in result["data"]}
        assert by_tag["trip"]["totalSpend"] == 50.0
        assert by_tag["dinner"]["totalSpend"] == 50.0
        assert by_tag["trip"]["transactionCount"] == 1

    def test_sorted_by_spend_descending(self):
        rows = [
            _row(1, -10.0, "Food & drink", tags="small"),
            _row(2, -100.0, "Travel", tags="big"),
        ]
        db = _make_mock_db(rows)
        result = asyncio.run(get_tags_overview(db=db))
        assert [d["tagName"] for d in result["data"]] == ["big", "small"]

    def test_query_filters_excluded_transactions(self):
        db = _make_mock_db([_row(1, -10.0, "Food & drink", tags="trip")])
        asyncio.run(get_tags_overview(db=db))
        _, kwargs = db.transactions.query.call_args
        assert kwargs["filters"] == {TransactionsTable.exclude.name: ("==", False)}


# ─── GET /tags/{tag_name} ───────────────────────────────────────────────────────

class TestGetTagDetail:
    def test_404_for_unknown_tag(self):
        db = _make_mock_db([_row(1, -10.0, "Food & drink", tags="other")])
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_tag_detail("trip", db=db))
        assert exc_info.value.status_code == 404

    def test_404_when_no_transactions(self):
        db = _make_mock_db()
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_tag_detail("trip", db=db))
        assert exc_info.value.status_code == 404

    def test_response_shape(self):
        rows = [_row(1, -50.0, "Food & drink", tags="trip")]
        db = _make_mock_db(rows)
        result = asyncio.run(get_tag_detail("trip", db=db))
        data = result["data"]
        assert data["tagName"] == "trip"
        assert "totalSpend" in data
        assert "transactionCount" in data
        assert "spendOverTime" in data
        assert "categoryBreakdown" in data
        assert "transactions" in data

    def test_total_spend_and_transaction_count(self):
        rows = [
            _row(1, -50.0, "Food & drink", tags="trip", authorized_date="2025-01-10"),
            _row(2, -30.0, "Travel", tags="trip, flight", authorized_date="2025-01-15"),
            _row(3, -20.0, "Travel", tags="flight", authorized_date="2025-01-20"),
        ]
        db = _make_mock_db(rows)
        result = asyncio.run(get_tag_detail("trip", db=db))
        data = result["data"]
        assert data["totalSpend"] == 80.0
        assert data["transactionCount"] == 2

    def test_only_matching_tag_included_not_substring(self):
        rows = [
            _row(1, -50.0, "Food & drink", tags="trip"),
            _row(2, -30.0, "Travel", tags="trip-planning"),
        ]
        db = _make_mock_db(rows)
        result = asyncio.run(get_tag_detail("trip", db=db))
        assert result["data"]["transactionCount"] == 1

    def test_category_breakdown_grouped_by_primary_category(self):
        rows = [
            _row(1, -50.0, "Food & drink", tags="trip"),
            _row(2, -30.0, "Food & drink", tags="trip"),
            _row(3, -20.0, "Travel", tags="trip"),
        ]
        db = _make_mock_db(rows)
        result = asyncio.run(get_tag_detail("trip", db=db))
        breakdown = {b["categoryName"]: b for b in result["data"]["categoryBreakdown"]}
        assert breakdown["Food & drink"]["amount"] == 80.0
        assert breakdown["Food & drink"]["transactionCount"] == 2
        assert breakdown["Travel"]["amount"] == 20.0
        # Sorted by amount descending
        assert result["data"]["categoryBreakdown"][0]["categoryName"] == "Food & drink"

    def test_spend_over_time_zero_filled_across_range(self):
        rows = [
            _row(1, -50.0, "Food & drink", tags="trip", authorized_date="2025-01-10"),
            _row(2, -30.0, "Travel", tags="trip", authorized_date="2025-03-15"),
        ]
        db = _make_mock_db(rows)
        result = asyncio.run(get_tag_detail("trip", db=db))
        spend_over_time = result["data"]["spendOverTime"]
        months = [p["month"] for p in spend_over_time]
        assert months == ["2025-01", "2025-02", "2025-03"]
        amounts = {p["month"]: p["amount"] for p in spend_over_time}
        assert amounts["2025-01"] == 50.0
        assert amounts["2025-02"] == 0.0
        assert amounts["2025-03"] == 30.0
