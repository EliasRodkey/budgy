#!python3
"""
Tests for AIClientService and NormalizationPlan types.

Covers:
    - NormalizationPlan: valid construction, field defaults
    - AmountTransform: all three enum values accepted
    - AIClientService.plan_csv: correct schema parsing from mocked Claude response
    - AIClientService: model reads from AI_MODEL env var, falls back to default
    - AIClientService: structured tool_use output parsed into NormalizationPlan
"""
import os
from unittest.mock import MagicMock, patch

import pytest

from backend.ai_modules.normalization_plan import AmountTransform, CategoryMapping, NormalizationPlan
from backend.ai_modules.ai_client_service import AIClientService, _DEFAULT_MODEL, REQUIRED_SCHEMA_FIELDS


# ── NormalizationPlan types ───────────────────────────────────────────────────

class TestNormalizationPlan:
    def test_constructs_with_all_fields(self):
        plan = NormalizationPlan(
            column_map={"Txn Date": "authorized_date", "Debit": "amount"},
            category_map={"Dining": CategoryMapping(primary="Food & drink", detailed="Restaurants & bars")},
            amount_transform=AmountTransform.INVERT,
            issues=["ambiguous date format"],
            unmapped_required_columns=[],
        )
        assert plan.column_map["Txn Date"] == "authorized_date"
        assert plan.category_map["Dining"].primary == "Food & drink"
        assert plan.amount_transform == AmountTransform.INVERT

    def test_defaults_to_empty_lists(self):
        plan = NormalizationPlan(
            column_map={},
            category_map={},
            amount_transform=AmountTransform.SIGNED,
        )
        assert plan.issues == []
        assert plan.unmapped_required_columns == []
        assert plan.debit_column is None
        assert plan.credit_column is None

    def test_debit_credit_fields_stored(self):
        plan = NormalizationPlan(
            column_map={},
            category_map={},
            amount_transform=AmountTransform.DEBIT_CREDIT,
            debit_column="Debit Amount",
            credit_column="Credit Amount",
        )
        assert plan.debit_column == "Debit Amount"
        assert plan.credit_column == "Credit Amount"

    def test_column_map_accepts_null_values(self):
        plan = NormalizationPlan(
            column_map={"Unknown Col": None},
            category_map={},
            amount_transform=AmountTransform.SIGNED,
        )
        assert plan.column_map["Unknown Col"] is None

    def test_amount_transform_all_values_valid(self):
        for value in ("signed", "invert", "debit_credit"):
            plan = NormalizationPlan(
                column_map={},
                category_map={},
                amount_transform=AmountTransform(value),
            )
            assert plan.amount_transform.value == value


# ── AIClientService model selection ──────────────────────────────────────────

class TestAIClientServiceModelSelection:
    def test_uses_default_model_when_no_env_var(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("AI_MODEL", None)
            svc = AIClientService()
            assert svc.model == _DEFAULT_MODEL

    def test_reads_model_from_env_var(self):
        with patch.dict(os.environ, {"AI_MODEL": "claude-sonnet-4-6"}):
            svc = AIClientService()
            assert svc.model == "claude-sonnet-4-6"

    def test_constructor_arg_overrides_env_var(self):
        with patch.dict(os.environ, {"AI_MODEL": "claude-sonnet-4-6"}):
            svc = AIClientService(model="claude-haiku-4-5-20251001")
            assert svc.model == "claude-haiku-4-5-20251001"


# ── AIClientService.plan_csv ──────────────────────────────────────────────────

def _make_mock_response(tool_input: dict) -> MagicMock:
    """Build a mock Anthropic messages.create response with a tool_use block."""
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.input = tool_input

    response = MagicMock()
    response.content = [tool_block]
    return response


class TestAIClientServicePlanCsv:
    def _make_service(self, mock_create):
        svc = AIClientService(api_key="test-key")
        svc._client.messages.create = mock_create
        return svc

    def test_column_map_parsed_correctly(self):
        mock_create = MagicMock(return_value=_make_mock_response({
            "column_map": {"Txn Date": "authorized_date", "Amount": "amount"},
            "category_map": {},
            "amount_transform": "signed",
            "debit_column": None,
            "credit_column": None,
            "issues": [],
            "unmapped_required_columns": [],
        }))
        svc = self._make_service(mock_create)
        plan = svc.plan_csv(["Txn Date", "Amount"], [])

        assert plan.column_map["Txn Date"] == "authorized_date"
        assert plan.column_map["Amount"] == "amount"

    def test_category_map_parsed_into_category_mapping_objects(self):
        mock_create = MagicMock(return_value=_make_mock_response({
            "column_map": {},
            "category_map": {
                "Dining Out": {"primary": "Food & drink", "detailed": "Restaurants & bars"},
                "Gas": {"primary": "Transportation", "detailed": "Gas & EV charging"},
            },
            "amount_transform": "signed",
            "debit_column": None,
            "credit_column": None,
            "issues": [],
            "unmapped_required_columns": [],
        }))
        svc = self._make_service(mock_create)
        plan = svc.plan_csv([], ["Dining Out", "Gas"])

        assert isinstance(plan.category_map["Dining Out"], CategoryMapping)
        assert plan.category_map["Dining Out"].primary == "Food & drink"
        assert plan.category_map["Gas"].detailed == "Gas & EV charging"

    def test_amount_transform_invert_parsed(self):
        mock_create = MagicMock(return_value=_make_mock_response({
            "column_map": {},
            "category_map": {},
            "amount_transform": "invert",
            "debit_column": None,
            "credit_column": None,
            "issues": [],
            "unmapped_required_columns": [],
        }))
        svc = self._make_service(mock_create)
        plan = svc.plan_csv([], [])
        assert plan.amount_transform == AmountTransform.INVERT

    def test_debit_credit_columns_parsed(self):
        mock_create = MagicMock(return_value=_make_mock_response({
            "column_map": {},
            "category_map": {},
            "amount_transform": "debit_credit",
            "debit_column": "Debit",
            "credit_column": "Credit",
            "issues": [],
            "unmapped_required_columns": [],
        }))
        svc = self._make_service(mock_create)
        plan = svc.plan_csv(["Debit", "Credit"], [])
        assert plan.amount_transform == AmountTransform.DEBIT_CREDIT
        assert plan.debit_column == "Debit"
        assert plan.credit_column == "Credit"

    def test_unmapped_required_columns_passed_through(self):
        mock_create = MagicMock(return_value=_make_mock_response({
            "column_map": {"Date": "authorized_date"},
            "category_map": {},
            "amount_transform": "signed",
            "debit_column": None,
            "credit_column": None,
            "issues": ["Cannot determine amount column"],
            "unmapped_required_columns": ["amount", "primary_category"],
        }))
        svc = self._make_service(mock_create)
        plan = svc.plan_csv(["Date", "Description"], [])
        assert "amount" in plan.unmapped_required_columns
        assert "primary_category" in plan.unmapped_required_columns
        assert len(plan.issues) == 1

    def test_claude_called_with_correct_tool_choice(self):
        mock_create = MagicMock(return_value=_make_mock_response({
            "column_map": {},
            "category_map": {},
            "amount_transform": "signed",
            "debit_column": None,
            "credit_column": None,
            "issues": [],
            "unmapped_required_columns": [],
        }))
        svc = self._make_service(mock_create)
        svc.plan_csv(["Date"], ["Food"])

        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["tool_choice"] == {"type": "tool", "name": "return_normalization_plan"}
        assert call_kwargs["model"] == svc.model
