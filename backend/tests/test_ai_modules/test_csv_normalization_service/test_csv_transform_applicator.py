#!python3
"""
Tests for CSVTransformApplicator (apply_normalization_plan).

Covers:
    - Column renames applied correctly across all rows
    - Category substitution writes both primary_category and detailed_category
    - signed: amount passed through as float, unchanged
    - invert: amount values negated
    - debit_credit: credit - debit merged into single signed amount
    - Rows missing required fields are imported as UNCHECKED with "Other" fallback
    - Structurally corrupt rows (wrong column count, empty) are skipped
    - Valid rows returned cleanly without modification
"""
import pytest

from backend.ai_modules.csv_normalization_service.normalization_plan import AmountTransform, CategoryMapping, NormalizationPlan
from backend.ai_modules.csv_normalization_service.csv_transform_applicator import apply_normalization_plan


def _make_plan(**kwargs) -> NormalizationPlan:
    defaults = dict(
        column_map={},
        category_map={},
        amount_transform=AmountTransform.EXPENSE_NEGATIVE,
    )
    defaults.update(kwargs)
    return NormalizationPlan(**defaults)


# ── Column renames ─────────────────────────────────────────────────────────────

class TestColumnRenames:
    def test_renames_columns_across_all_rows(self):
        rows = [
            {"Txn Date": "2024-01-15", "Merchant": "Chipotle", "Category": "Food", "Amount": "-15.50"},
            {"Txn Date": "2024-01-16", "Merchant": "Amazon", "Category": "Shopping", "Amount": "-42.00"},
        ]
        plan = _make_plan(
            column_map={
                "Txn Date": "authorized_date",
                "Merchant": "description",
                "Category": "primary_category",
                "Amount": "amount",
            },
            amount_transform=AmountTransform.EXPENSE_NEGATIVE,
        )
        result, _ = apply_normalization_plan(rows, plan)

        assert result[0]["authorized_date"] == "2024-01-15"
        assert result[0]["description"] == "Chipotle"
        assert result[1]["authorized_date"] == "2024-01-16"
        assert result[1]["description"] == "Amazon"

    def test_raw_keys_absent_from_output(self):
        rows = [{"Txn Date": "2024-01-15", "Merchant": "Test", "Category": "Food", "Amount": "-1.00"}]
        plan = _make_plan(
            column_map={
                "Txn Date": "authorized_date",
                "Merchant": "description",
                "Category": "primary_category",
                "Amount": "amount",
            },
        )
        result, _ = apply_normalization_plan(rows, plan)
        assert "Txn Date" not in result[0]
        assert "Merchant" not in result[0]

    def test_null_mapped_column_dropped(self):
        rows = [
            {
                "authorized_date": "2024-01-15",
                "description": "Test",
                "primary_category": "Food",
                "amount": "-5.00",
                "Unknown": "garbage",
            }
        ]
        plan = _make_plan(column_map={"Unknown": None})
        result, _ = apply_normalization_plan(rows, plan)
        assert "Unknown" not in result[0]

    def test_existing_schema_field_headers_passed_through(self):
        rows = [
            {
                "authorized_date": "2024-01-15",
                "description": "Test",
                "primary_category": "Food",
                "amount": "-5.00",
            }
        ]
        plan = _make_plan()
        result, _ = apply_normalization_plan(rows, plan)
        assert result[0]["authorized_date"] == "2024-01-15"
        assert result[0]["description"] == "Test"


# ── Category substitution ──────────────────────────────────────────────────────

class TestCategorySubstitution:
    def _base_row(self, category: str) -> dict:
        return {
            "authorized_date": "2024-01-15",
            "description": "Chipotle",
            "primary_category": category,
            "amount": "-15.50",
        }

    def test_sets_primary_and_detailed_category(self):
        rows = [self._base_row("Dining Out")]
        plan = _make_plan(
            category_map={
                "Dining Out": CategoryMapping(
                    primary="Food & drink", detailed="Restaurants & bars"
                )
            }
        )
        result, _ = apply_normalization_plan(rows, plan)
        assert result[0]["primary_category"] == "Food & drink"
        assert result[0]["detailed_category"] == "Restaurants & bars"

    def test_unmapped_category_passes_through(self):
        rows = [self._base_row("Unknown Category")]
        plan = _make_plan(category_map={})
        result, _ = apply_normalization_plan(rows, plan)
        assert result[0]["primary_category"] == "Unknown Category"
        assert "detailed_category" not in result[0]

    def test_substitution_applies_to_all_rows(self):
        rows = [self._base_row("Gas"), self._base_row("Gas")]
        plan = _make_plan(
            category_map={
                "Gas": CategoryMapping(
                    primary="Transportation", detailed="Gas & EV charging"
                )
            }
        )
        result, _ = apply_normalization_plan(rows, plan)
        assert result[0]["primary_category"] == "Transportation"
        assert result[1]["primary_category"] == "Transportation"


# ── Amount normalization ───────────────────────────────────────────────────────

class TestAmountSigned:
    def _row(self, amount: str) -> dict:
        return {
            "authorized_date": "2024-01-15",
            "description": "Test",
            "primary_category": "Food",
            "amount": amount,
        }

    def test_signed_passthrough_negative(self):
        result, _ = apply_normalization_plan([self._row("-15.50")], _make_plan())
        assert result[0]["amount"] == -15.50

    def test_signed_passthrough_positive(self):
        result, _ = apply_normalization_plan([self._row("100.00")], _make_plan())
        assert result[0]["amount"] == 100.00

    def test_signed_amount_is_float(self):
        result, _ = apply_normalization_plan([self._row("-15.50")], _make_plan())
        assert isinstance(result[0]["amount"], float)


class TestAmountInvert:
    def _row(self, amount: str) -> dict:
        return {
            "authorized_date": "2024-01-15",
            "description": "Test",
            "primary_category": "Food",
            "amount": amount,
        }

    def test_invert_negates_positive_amount(self):
        plan = _make_plan(amount_transform=AmountTransform.EXPENSE_POSITIVE)
        result, _ = apply_normalization_plan([self._row("15.50")], plan)
        assert result[0]["amount"] == -15.50

    def test_invert_negates_negative_amount(self):
        plan = _make_plan(amount_transform=AmountTransform.EXPENSE_POSITIVE)
        result, _ = apply_normalization_plan([self._row("-15.50")], plan)
        assert result[0]["amount"] == 15.50


class TestAmountDebitCredit:
    def _row(self, debit: str, credit: str) -> dict:
        return {
            "authorized_date": "2024-01-15",
            "description": "Test",
            "primary_category": "Food",
            "Debit": debit,
            "Credit": credit,
        }

    def _plan(self) -> NormalizationPlan:
        return _make_plan(
            amount_transform=AmountTransform.DEBIT_CREDIT,
            debit_column="Debit",
            credit_column="Credit",
        )

    def test_debit_only_produces_negative_amount(self):
        result, _ = apply_normalization_plan([self._row("15.50", "")], self._plan())
        assert result[0]["amount"] == pytest.approx(-15.50)

    def test_credit_only_produces_positive_amount(self):
        result, _ = apply_normalization_plan([self._row("", "2000.00")], self._plan())
        assert result[0]["amount"] == pytest.approx(2000.00)

    def test_debit_and_credit_computes_net(self):
        result, _ = apply_normalization_plan([self._row("10.00", "5.00")], self._plan())
        assert result[0]["amount"] == pytest.approx(-5.00)

    def test_both_empty_produces_zero(self):
        result, _ = apply_normalization_plan([self._row("", "")], self._plan())
        assert result[0]["amount"] == pytest.approx(0.0)


# ── Soft failures (missing required fields) ────────────────────────────────────

class TestSoftFailures:
    def _valid_row(self) -> dict:
        return {
            "authorized_date": "2024-01-15",
            "description": "Test",
            "primary_category": "Food",
            "amount": "-5.00",
        }

    def test_missing_category_imports_as_unchecked_with_other(self):
        rows = [{"authorized_date": "2024-01-15", "description": "Test", "amount": "-5.00"}]
        result, skipped = apply_normalization_plan(rows, _make_plan())
        assert len(result) == 1
        assert len(skipped) == 0
        assert result[0]["status"] == "Unchecked"
        assert result[0]["primary_category"] == "Other"

    def test_missing_amount_imports_as_unchecked(self):
        rows = [{"authorized_date": "2024-01-15", "description": "Test", "primary_category": "Food"}]
        result, skipped = apply_normalization_plan(rows, _make_plan())
        assert len(result) == 1
        assert result[0]["status"] == "Unchecked"

    def test_valid_rows_not_marked_unchecked(self):
        rows = [self._valid_row()]
        result, _ = apply_normalization_plan(rows, _make_plan())
        assert result[0].get("status") != "Unchecked"

    def test_valid_rows_returned_cleanly(self):
        rows = [self._valid_row(), self._valid_row()]
        result, skipped = apply_normalization_plan(rows, _make_plan())
        assert len(result) == 2
        assert len(skipped) == 0


# ── Skipped rows (structurally corrupt) ───────────────────────────────────────

class TestSkippedRows:
    def _valid_row(self) -> dict:
        return {
            "authorized_date": "2024-01-15",
            "description": "Test",
            "primary_category": "Food",
            "amount": "-5.00",
        }

    def test_empty_row_is_skipped(self):
        rows = [
            self._valid_row(),
            {"authorized_date": "", "description": "", "primary_category": "", "amount": ""},
        ]
        result, skipped = apply_normalization_plan(rows, _make_plan())
        assert len(result) == 1
        assert len(skipped) == 1
        assert skipped[0]["row"] == 2
        assert skipped[0]["reason"] == "empty row"

    def test_wrong_column_count_row_is_skipped(self):
        rows = [
            self._valid_row(),
            {"authorized_date": "2024-01-15", "description": "Test"},  # missing cols
        ]
        result, skipped = apply_normalization_plan(rows, _make_plan())
        assert len(result) == 1
        assert len(skipped) == 1
        assert skipped[0]["reason"] == "wrong column count"

    def test_skipped_row_numbers_are_1_indexed(self):
        rows = [
            {"authorized_date": "", "description": "", "primary_category": "", "amount": ""},
        ]
        _, skipped = apply_normalization_plan(rows, _make_plan())
        assert skipped[0]["row"] == 1
