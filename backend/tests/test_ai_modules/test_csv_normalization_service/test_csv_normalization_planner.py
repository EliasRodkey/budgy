#!python3
"""
Tests for CSVNormalizationPlanner.

Covers:
    - Exact Budgy column names: empty column_map, no AI call
    - All categories in cache: plan returned without calling AIClientService
    - Partial cache hit: only uncached items sent to AI
    - Missing primary_category: populates unmapped_required_columns
    - AI and cache results merged correctly into a single NormalizationPlan
    - Debit/credit pattern: AI called, amount_transform set to DEBIT_CREDIT
"""
from unittest.mock import MagicMock, call

import pytest

from backend.ai_modules.csv_normalization_service.normalization_plan import AmountTransform, CategoryMapping, NormalizationPlan
from backend.ai_modules.csv_normalization_service.csv_normalization_service import REQUIRED_SCHEMA_FIELDS
from backend.ai_modules.csv_normalization_service.csv_normalization_planner import CSVNormalizationPlanner


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_ai_plan(**kwargs) -> NormalizationPlan:
    defaults = dict(
        column_map={},
        category_map={},
        amount_transform=AmountTransform.EXPENSE_NEGATIVE,
        debit_column=None,
        credit_column=None,
        issues=[],
        unmapped_required_columns=[],
    )
    defaults.update(kwargs)
    return NormalizationPlan(**defaults)


def _make_planner(
    col_rules: dict[str, str | None] = None,
    cat_rules: dict[str, dict | None] = None,
    ai_plan: NormalizationPlan = None,
) -> CSVNormalizationPlanner:
    """
    Build a CSVNormalizationPlanner with mocked dependencies.

    col_rules: maps raw_header -> schema_field (or None for cache miss)
    cat_rules: maps raw_category -> {primary, detailed} dict (or None for cache miss)
    ai_plan: what AIClientService.plan_csv returns
    """
    col_rules = col_rules or {}
    cat_rules = cat_rules or {}

    rules_manager = MagicMock()
    rules_manager.get_column_rule.side_effect = lambda h: col_rules.get(h)
    rules_manager.get_category_rule.side_effect = lambda c: cat_rules.get(c)

    ai_service = MagicMock()
    ai_service.plan_csv.return_value = ai_plan or _make_ai_plan()

    return CSVNormalizationPlanner(rules_manager, ai_service)


# ── Exact-match fast path ──────────────────────────────────────────────────────

class TestExactMatchFastPath:
    """CSV with all column headers already matching Budgy schema fields."""

    EXACT_HEADERS = ["authorized_date", "description", "primary_category", "amount"]

    def test_column_map_is_empty(self):
        planner = _make_planner()
        plan, _ = planner.plan(self.EXACT_HEADERS, [])
        assert plan.column_map == {}

    def test_no_ai_call(self):
        planner = _make_planner()
        planner.plan(self.EXACT_HEADERS, [])
        planner._ai.plan_csv.assert_not_called()

    def test_amount_transform_is_signed(self):
        planner = _make_planner()
        plan, _ = planner.plan(self.EXACT_HEADERS, [])
        assert plan.amount_transform == AmountTransform.EXPENSE_NEGATIVE

    def test_no_unmapped_required_columns(self):
        planner = _make_planner()
        plan, _ = planner.plan(self.EXACT_HEADERS, [])
        assert plan.unmapped_required_columns == []


# ── Full cache hit ─────────────────────────────────────────────────────────────

class TestFullCacheHit:
    """All headers in rules cache, all categories in rules cache."""

    def test_no_ai_call_when_all_cached(self):
        planner = _make_planner(
            col_rules={
                "Txn Date": "authorized_date",
                "Merchant": "description",
                "Category": "primary_category",
                "Amount": "amount",
            },
            cat_rules={
                "Dining Out": {"primary": "Food & drink", "detailed": "Restaurants & bars"},
            },
        )
        planner.plan(["Txn Date", "Merchant", "Category", "Amount"], ["Dining Out"])
        planner._ai.plan_csv.assert_not_called()

    def test_used_cache_true_on_full_cache_hit(self):
        planner = _make_planner(
            col_rules={
                "Txn Date": "authorized_date",
                "Merchant": "description",
                "Category": "primary_category",
                "Amount": "amount",
            },
        )
        _, used_cache = planner.plan(["Txn Date", "Merchant", "Category", "Amount"], [])
        assert used_cache is True

    def test_column_map_built_from_cache(self):
        planner = _make_planner(
            col_rules={
                "Txn Date": "authorized_date",
                "Merchant": "description",
                "Category": "primary_category",
                "Amount": "amount",
            },
        )
        plan, _ = planner.plan(["Txn Date", "Merchant", "Category", "Amount"], [])
        assert plan.column_map["Txn Date"] == "authorized_date"
        assert plan.column_map["Amount"] == "amount"

    def test_category_map_built_from_cache(self):
        planner = _make_planner(
            col_rules={
                "Date": "authorized_date",
                "Desc": "description",
                "Cat": "primary_category",
                "Amt": "amount",
            },
            cat_rules={
                "Dining Out": {"primary": "Food & drink", "detailed": "Restaurants & bars"},
            },
        )
        plan, _ = planner.plan(["Date", "Desc", "Cat", "Amt"], ["Dining Out"])
        assert isinstance(plan.category_map["Dining Out"], CategoryMapping)
        assert plan.category_map["Dining Out"].primary == "Food & drink"


# ── Partial cache hit ──────────────────────────────────────────────────────────

class TestPartialCacheHit:
    """Some items cached, others need AI."""

    def test_only_uncached_headers_sent_to_ai(self):
        planner = _make_planner(
            col_rules={"Txn Date": "authorized_date"},  # one header cached
            ai_plan=_make_ai_plan(
                column_map={
                    "Merchant": "description",
                    "Category": "primary_category",
                    "Amount": "amount",
                }
            ),
        )
        planner.plan(["Txn Date", "Merchant", "Category", "Amount"], [])

        ai_headers = planner._ai.plan_csv.call_args[0][0]
        assert "Txn Date" not in ai_headers
        assert "Merchant" in ai_headers

    def test_used_cache_false_when_ai_called(self):
        planner = _make_planner(
            col_rules={"Txn Date": "authorized_date"},
            ai_plan=_make_ai_plan(
                column_map={
                    "Merchant": "description",
                    "Category": "primary_category",
                    "Amount": "amount",
                }
            ),
        )
        _, used_cache = planner.plan(["Txn Date", "Merchant", "Category", "Amount"], [])
        assert used_cache is False

    def test_only_uncached_categories_sent_to_ai(self):
        planner = _make_planner(
            col_rules={
                "Date": "authorized_date",
                "Desc": "description",
                "Cat": "primary_category",
                "Amt": "amount",
            },
            cat_rules={"Gas": {"primary": "Transportation", "detailed": "Gas & EV charging"}},
            ai_plan=_make_ai_plan(
                category_map={
                    "Dining Out": CategoryMapping(primary="Food & drink", detailed="Restaurants & bars")
                }
            ),
        )
        planner.plan(["Date", "Desc", "Cat", "Amt"], ["Gas", "Dining Out"])

        ai_categories = planner._ai.plan_csv.call_args[0][1]
        assert "Gas" not in ai_categories
        assert "Dining Out" in ai_categories

    def test_cache_and_ai_merged_into_single_plan(self):
        planner = _make_planner(
            col_rules={"Txn Date": "authorized_date"},
            ai_plan=_make_ai_plan(
                column_map={
                    "Merchant": "description",
                    "Category": "primary_category",
                    "Amount": "amount",
                }
            ),
        )
        plan, _ = planner.plan(["Txn Date", "Merchant", "Category", "Amount"], [])
        assert plan.column_map["Txn Date"] == "authorized_date"
        assert plan.column_map["Merchant"] == "description"
        assert plan.column_map["Amount"] == "amount"


# ── Missing required columns ───────────────────────────────────────────────────

class TestMissingRequiredColumns:
    def test_missing_primary_category_in_unmapped_required(self):
        # No header maps to primary_category, AI also returns nothing for it
        planner = _make_planner(
            ai_plan=_make_ai_plan(
                column_map={
                    "Date": "authorized_date",
                    "Desc": "description",
                    "Amt": "amount",
                    # no primary_category mapping
                }
            ),
        )
        plan, _ = planner.plan(["Date", "Desc", "Amt"], [])
        assert "primary_category" in plan.unmapped_required_columns

    def test_all_required_mapped_means_no_unmapped_required(self):
        planner = _make_planner(
            ai_plan=_make_ai_plan(
                column_map={
                    "Date": "authorized_date",
                    "Desc": "description",
                    "Cat": "primary_category",
                    "Amt": "amount",
                }
            ),
        )
        plan, _ = planner.plan(["Date", "Desc", "Cat", "Amt"], [])
        assert plan.unmapped_required_columns == []

    def test_multiple_unmapped_required_fields_listed(self):
        planner = _make_planner(
            ai_plan=_make_ai_plan(
                column_map={"Date": "authorized_date"},  # only date mapped
                unmapped_required_columns=["description", "primary_category", "amount"],
            ),
        )
        plan, _ = planner.plan(["Date", "Unknown1", "Unknown2"], [])
        assert "description" in plan.unmapped_required_columns
        assert "primary_category" in plan.unmapped_required_columns
        assert "amount" in plan.unmapped_required_columns


# ── Debit/credit detection ─────────────────────────────────────────────────────

class TestDebitCreditDetection:
    def test_debit_credit_headers_trigger_ai_call(self):
        planner = _make_planner(
            ai_plan=_make_ai_plan(
                column_map={
                    "Date": "authorized_date",
                    "Desc": "description",
                    "Cat": "primary_category",
                },
                amount_transform=AmountTransform.DEBIT_CREDIT,
                debit_column="Debit",
                credit_column="Credit",
            ),
        )
        planner.plan(["Date", "Desc", "Cat", "Debit", "Credit"], [])
        planner._ai.plan_csv.assert_called_once()

    def test_amount_transform_set_to_debit_credit(self):
        planner = _make_planner(
            ai_plan=_make_ai_plan(
                column_map={
                    "Date": "authorized_date",
                    "Desc": "description",
                    "Cat": "primary_category",
                },
                amount_transform=AmountTransform.DEBIT_CREDIT,
                debit_column="Debit",
                credit_column="Credit",
            ),
        )
        plan, _ = planner.plan(["Date", "Desc", "Cat", "Debit", "Credit"], [])
        assert plan.amount_transform == AmountTransform.DEBIT_CREDIT
        assert plan.debit_column == "Debit"
        assert plan.credit_column == "Credit"
