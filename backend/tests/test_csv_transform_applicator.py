#!python3
"""
Tests for CSVTransformApplicator (apply_normalization_plan).

Covers:
    - Column renames applied correctly across all rows
    - Category substitution writes both primary_category and detailed_category
    - signed: amount passed through as float, unchanged
    - invert: amount values negated
    - debit_credit: credit - debit merged into single signed amount
    - Rows missing required fields raise TransformValidationError with correct metadata
    - Valid rows returned cleanly without modification
"""
import pytest

from backend.ai_modules.normalization_plan import AmountTransform, CategoryMapping, NormalizationPlan
from backend.ai_modules.csv_transform_applicator import (
    TransformValidationError,
    apply_normalization_plan,
)


def _make_plan(**kwargs) -> NormalizationPlan:
    defaults = dict(
        column_map={},
        category_map={},
        amount_transform=AmountTransform.SIGNED,
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
            amount_transform=AmountTransform.SIGNED,
        )
        result = apply_normalization_plan(rows, plan)

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
        result = apply_normalization_plan(rows, plan)
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
        result = apply_normalization_plan(rows, plan)
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
        result = apply_normalization_plan(rows, plan)
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
        result = apply_normalization_plan(rows, plan)
        assert result[0]["primary_category"] == "Food & drink"
        assert result[0]["detailed_category"] == "Restaurants & bars"

    def test_unmapped_category_passes_through(self):
        rows = [self._base_row("Unknown Category")]
        plan = _make_plan(category_map={})
        result = apply_normalization_plan(rows, plan)
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
        result = apply_normalization_plan(rows, plan)
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
        result = apply_normalization_plan([self._row("-15.50")], _make_plan())
        assert result[0]["amount"] == -15.50

    def test_signed_passthrough_positive(self):
        result = apply_normalization_plan([self._row("100.00")], _make_plan())
        assert result[0]["amount"] == 100.00

    def test_signed_amount_is_float(self):
        result = apply_normalization_plan([self._row("-15.50")], _make_plan())
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
        plan = _make_plan(amount_transform=AmountTransform.INVERT)
        result = apply_normalization_plan([self._row("15.50")], plan)
        assert result[0]["amount"] == -15.50

    def test_invert_negates_negative_amount(self):
        plan = _make_plan(amount_transform=AmountTransform.INVERT)
        result = apply_normalization_plan([self._row("-15.50")], plan)
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
        result = apply_normalization_plan([self._row("15.50", "")], self._plan())
        assert result[0]["amount"] == pytest.approx(-15.50)

    def test_credit_only_produces_positive_amount(self):
        result = apply_normalization_plan([self._row("", "2000.00")], self._plan())
        assert result[0]["amount"] == pytest.approx(2000.00)

    def test_debit_and_credit_computes_net(self):
        result = apply_normalization_plan([self._row("10.00", "5.00")], self._plan())
        assert result[0]["amount"] == pytest.approx(-5.00)

    def test_both_empty_produces_zero(self):
        result = apply_normalization_plan([self._row("", "")], self._plan())
        assert result[0]["amount"] == pytest.approx(0.0)


# ── Validation errors ──────────────────────────────────────────────────────────

class TestTransformValidationError:
    def _valid_row(self) -> dict:
        return {
            "authorized_date": "2024-01-15",
            "description": "Test",
            "primary_category": "Food",
            "amount": "-5.00",
        }

    def test_raises_when_row_missing_required_field(self):
        rows = [{"authorized_date": "2024-01-15", "description": "Test", "amount": "-5.00"}]
        plan = _make_plan()
        with pytest.raises(TransformValidationError) as exc:
            apply_normalization_plan(rows, plan)
        assert exc.value.failed_rows[0]["row_index"] == 0
        assert "primary_category" in exc.value.failed_rows[0]["missing_fields"]

    def test_raises_lists_all_failed_rows(self):
        good = self._valid_row()
        bad1 = {"authorized_date": "2024-01-15", "description": "A", "amount": "-1.00"}
        bad2 = {"authorized_date": "2024-01-16", "primary_category": "Food", "amount": "-2.00"}
        plan = _make_plan()
        with pytest.raises(TransformValidationError) as exc:
            apply_normalization_plan([good, bad1, bad2], plan)
        indices = [r["row_index"] for r in exc.value.failed_rows]
        assert 1 in indices
        assert 2 in indices
        assert 0 not in indices

    def test_error_message_includes_count(self):
        bad = {"authorized_date": "2024-01-15"}
        plan = _make_plan()
        with pytest.raises(TransformValidationError) as exc:
            apply_normalization_plan([bad], plan)
        assert "1" in str(exc.value)

    def test_valid_rows_returned_cleanly(self):
        rows = [self._valid_row(), self._valid_row()]
        plan = _make_plan()
        result = apply_normalization_plan(rows, plan)
        assert len(result) == 2
