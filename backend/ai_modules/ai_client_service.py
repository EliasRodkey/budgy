#!python3
import json
import os
from typing import Optional

import anthropic

from backend.ai_modules.normalization_plan import AmountTransform, CategoryMapping, NormalizationPlan
from backend.utils.analysis_utils import DetailedCategories, PrimaryCategories

from pleasant_loggers import get_logger
logger = get_logger(__name__)

_DEFAULT_MODEL = "claude-haiku-4-5-20251001"

# Schema fields the AI can map CSV columns to
REQUIRED_SCHEMA_FIELDS = ["authorized_date", "description", "primary_category", "amount"]
OPTIONAL_SCHEMA_FIELDS = [
    "posted_date", "status", "account_name", "detailed_category", "notes", "tags"
]
ALL_SCHEMA_FIELDS = REQUIRED_SCHEMA_FIELDS + OPTIONAL_SCHEMA_FIELDS

# Tool schema for Claude's structured output
_NORMALIZATION_TOOL = {
    "name": "return_normalization_plan",
    "description": (
        "Return a plan for normalizing a CSV file to the Budgy transaction schema. "
        "Map each CSV column header to a schema field, map each raw category value to "
        "a valid primary+detailed category pair, and detect the amount sign convention."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "column_map": {
                "type": "object",
                "description": (
                    "Maps each raw CSV header to a Budgy schema field name, or null if unmappable. "
                    f"Valid schema fields: {ALL_SCHEMA_FIELDS}"
                ),
                "additionalProperties": {"type": ["string", "null"]},
            },
            "category_map": {
                "type": "object",
                "description": "Maps each raw category string to primary and detailed Budgy categories.",
                "additionalProperties": {
                    "type": "object",
                    "properties": {
                        "primary": {"type": "string"},
                        "detailed": {"type": "string"},
                    },
                    "required": ["primary", "detailed"],
                },
            },
            "amount_transform": {
                "type": "string",
                "enum": ["signed", "invert", "debit_credit"],
                "description": (
                    "How to interpret the amount column(s). Use sample numeric values to decide:\n"
                    "HINT: Income usually made up of fewer, larger values; expenses usually more frequent and smaller."
                    "Income may also come from peer to peer services (Venmo, MBway, cashapp, zelle, gcash, etc.)\n"
                    "'signed': single column where expenses are negative and income/credits are positive "
                    "(e.g. samples [-4.50, -12.30, 500.00] — spending negative, paycheck positive).\n"
                    "'invert': single column where expenses are positive and income is negative "
                    "(e.g. samples [4.50, 12.30, -500.00] — spending positive, paycheck negative). "
                    "If most values are positive and any large negative value looks like income, choose 'invert'.\n"
                    "'debit_credit': two separate columns for debits and credits."
                ),
            },
            "debit_column": {
                "type": ["string", "null"],
                "description": "The debit column header when amount_transform is 'debit_credit'.",
            },
            "credit_column": {
                "type": ["string", "null"],
                "description": "The credit column header when amount_transform is 'debit_credit'.",
            },
            "issues": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Any problems or ambiguities found in the CSV structure.",
            },
            "unmapped_required_columns": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    f"Required schema fields that could not be mapped: {REQUIRED_SCHEMA_FIELDS}. "
                    "Include a field name here if no CSV column could be confidently mapped to it."
                ),
            },
        },
        "required": [
            "column_map",
            "category_map",
            "amount_transform",
            "debit_column",
            "credit_column",
            "issues",
            "unmapped_required_columns",
        ],
    },
}

# Stable enum lists for prompt caching (these never change at runtime)
_PRIMARY_ENUM_TEXT = ", ".join(f'"{c.value}"' for c in PrimaryCategories)
_DETAILED_ENUM_TEXT = "\n".join(
    f'  {pc.value}: [{", ".join(f"{dc.value!r}" for dc in dcs)}]'
    for pc, dcs in __import__(
        "backend.utils.analysis_utils", fromlist=["CATEGORY_MAPPING"]
    ).CATEGORY_MAPPING.items()
)


def _build_system_prompt() -> list[dict]:
    """
    Build the system prompt as a list of content blocks.
    The enum block uses cache_control so repeated calls hit the prompt cache.
    """
    return [
        {
            "type": "text",
            "text": (
                "You are a CSV normalization assistant for a personal finance app called Budgy. "
                "Your job is to analyze a CSV's headers and unique category values, then produce "
                "a normalization plan that maps them to Budgy's transaction schema.\n\n"
                "Rules:\n"
                "COLUMN MAPPING:\n"
                "- Map each column header to the closest matching schema field. Use null if no reasonable match exists.\n"
                "- If a column's header or values suggest it contains payment methods or account names "
                "(e.g. 'MOP', 'Method of Payment', 'Account', 'Card', 'Institution'), map it to "
                "'account_name' in column_map — these are valid schema fields even though their values "
                "are not spending categories.\n"
                "CATEGORY MAPPING:\n"
                "- Map raw category strings to the most specific valid primary+detailed category pair.\n"
                "- Only include a value in category_map if it is clearly a spending or income category "
                "(e.g. 'Groceries', 'Gas Station', 'Salary'). Do NOT add payment method names, bank names, "
                "card names, or institution identifiers to category_map — omit those entirely.\n"
                "SIGN DETECTION:\n"
                "- Use the sample numeric values provided to detect the sign convention of the amount column.\n"
                "- If expenses are negative and income is positive → 'signed'.\n"
                "- If expenses are positive and income is negative → 'invert'.\n"
                "- If there are separate debit and credit columns → 'debit_credit'.\n"
                "OTHER:\n"
                "- List any unmappable required fields in unmapped_required_columns.\n"
                "- Make a best-effort mapping. If unsure, make your best guess and add the uncertainty to the issues field rather than returning null."
            ),
        },
        {
            "type": "text",
            "text": (
                f"Valid Budgy schema fields: {ALL_SCHEMA_FIELDS}\n\n"
                f"Valid primary categories: [{_PRIMARY_ENUM_TEXT}]\n\n"
                f"Category hierarchy (primary: [detailed options]):\n{_DETAILED_ENUM_TEXT}"
            ),
            "cache_control": {"type": "ephemeral"},
        },
    ]


class AIClientService:
    """
    Abstraction layer over the Anthropic SDK for CSV normalization.

    Calls Claude with tool_use structured output to return a NormalizationPlan.
    Model defaults to the AI_MODEL env var or claude-haiku-4-5-20251001.

    Designed for future extension: user-supplied API keys and model selection
    can be added by passing them at construction time.
    """

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        self.model = model or os.environ.get("AI_MODEL", _DEFAULT_MODEL)
        self._client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )

    def plan_csv(
        self,
        headers: list[str],
        unique_categories: list[str],
        sample_amount_values: dict[str, list[float]] | None = None,
    ) -> NormalizationPlan:
        """
        Analyze CSV headers and unique category values, return a NormalizationPlan.

        Args:
            headers: Raw column header strings from the CSV.
            unique_categories: Unique values found in any category-like column.

        Returns:
            NormalizationPlan with column_map, category_map, amount_transform, and issues.
        """
        user_parts = [
            f"CSV headers: {json.dumps(headers)}",
            f"Unique category values found in the CSV: {json.dumps(unique_categories)}",
        ]
        if sample_amount_values:
            user_parts.append(
                f"Sample numeric values per column (use for sign convention detection): "
                f"{json.dumps(sample_amount_values)}"
            )
        user_text = "\n".join(user_parts)

        logger.info(
            f"Calling Claude ({self.model}) to plan CSV normalization "
            f"({len(headers)} headers, {len(unique_categories)} categories)"
        )

        response = self._client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=_build_system_prompt(),
            tools=[_NORMALIZATION_TOOL],
            tool_choice={"type": "tool", "name": "return_normalization_plan"},
            messages=[{"role": "user", "content": user_text}],
        )

        tool_use_block = next(
            b for b in response.content if b.type == "tool_use"
        )
        raw: dict = tool_use_block.input

        column_map: dict[str, Optional[str]] = raw.get("column_map", {})
        category_map = {
            k: CategoryMapping(primary=v["primary"], detailed=v["detailed"])
            for k, v in raw.get("category_map", {}).items()
        }

        logger.info(
            f"Plan received: {len(column_map)} column mappings, "
            f"{len(category_map)} category mappings"
        )

        return NormalizationPlan(
            column_map=column_map,
            category_map=category_map,
            amount_transform=AmountTransform(raw.get("amount_transform", "signed")),
            debit_column=raw.get("debit_column"),
            credit_column=raw.get("credit_column"),
            issues=raw.get("issues", []),
            unmapped_required_columns=raw.get("unmapped_required_columns", []),
        )
