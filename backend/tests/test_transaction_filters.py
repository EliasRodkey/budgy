#!python3
"""
Pure unit tests for TransactionFilters.to_db_filters() and sort_ascending.
No database, no HTTP client required.
"""
from datetime import datetime

import pytest

from backend.api.transactions.transactions_models import TransactionFilters
from backend.utils.analysis_utils import PrimaryCategories, DetailedCategories


def make_filters(**kwargs) -> TransactionFilters:
    defaults = dict(sort_by="date", sort_order="desc", page=1, page_size=20)
    defaults.update(kwargs)
    return TransactionFilters(**defaults)


# ── sort_ascending ─────────────────────────────────────────────────────────────

class TestSortAscending:
    def test_false_when_sort_order_desc(self):
        f = make_filters(sort_order="desc")
        assert f.sort_ascending is False

    def test_true_when_sort_order_asc(self):
        f = make_filters(sort_order="asc")
        assert f.sort_ascending is True


# ── to_db_filters ─────────────────────────────────────────────────────────────

class TestToDbFilters:
    def test_exclude_filter_present_by_default(self):
        filters, _ = make_filters().to_db_filters()
        assert "exclude" in filters
        assert filters["exclude"] == ("==", False)

    def test_exclude_filter_absent_when_show_excluded_true(self):
        filters, _ = make_filters(show_excluded=True).to_db_filters()
        assert "exclude" not in filters

    def test_valid_primary_category_included(self):
        category = PrimaryCategories.FOOD_AND_DRINK.value
        filters, _ = make_filters(primary_category=category).to_db_filters()
        assert filters["primary_category"] == ("==", category)

    def test_invalid_primary_category_excluded(self):
        filters, _ = make_filters(primary_category="not a real category").to_db_filters()
        assert "primary_category" not in filters

    def test_valid_detailed_category_included(self):
        category = DetailedCategories.GROCERIES.value
        filters, _ = make_filters(detailed_category=category).to_db_filters()
        assert filters["detailed_category"] == ("==", category)

    def test_invalid_detailed_category_excluded(self):
        filters, _ = make_filters(detailed_category="fake").to_db_filters()
        assert "detailed_category" not in filters

    def test_date_from_only_defaults_date_to_today(self):
        filters, _ = make_filters(date_from="2024-01-01").to_db_filters()
        assert "authorized_date" in filters
        op, (dt_from, dt_to) = filters["authorized_date"]
        assert op == "between"
        assert dt_from == datetime(2024, 1, 1)
        assert dt_to.date() == datetime.now().date()

    def test_date_to_only_defaults_date_from_1900(self):
        filters, _ = make_filters(date_to="2024-12-31").to_db_filters()
        op, (dt_from, dt_to) = filters["authorized_date"]
        assert dt_from == datetime(1900, 1, 1)
        assert dt_to == datetime(2024, 12, 31, 23, 59, 59)

    def test_both_dates_set(self):
        filters, _ = make_filters(date_from="2024-03-01", date_to="2024-03-31").to_db_filters()
        op, (dt_from, dt_to) = filters["authorized_date"]
        assert dt_from == datetime(2024, 3, 1)
        assert dt_to == datetime(2024, 3, 31, 23, 59, 59)

    def test_no_date_filter_when_neither_set(self):
        filters, _ = make_filters().to_db_filters()
        assert "authorized_date" not in filters

    def test_tags_parsed_to_list(self):
        _, tag_list = make_filters(tags="food,coffee").to_db_filters()
        assert tag_list == ["food", "coffee"]

    def test_tags_strips_whitespace(self):
        _, tag_list = make_filters(tags=" food , coffee ").to_db_filters()
        assert tag_list == ["food", "coffee"]

    def test_empty_tags_returns_empty_list(self):
        _, tag_list = make_filters(tags=None).to_db_filters()
        assert tag_list == []

    def test_tags_filters_empty_strings(self):
        _, tag_list = make_filters(tags=",,,").to_db_filters()
        assert tag_list == []
