#!python3
"""
backend.ai_modules.csv_normalization_service
AI service for CSV column/category normalization.
Renamed from ai_client_service.py; inherits AnthropicClient.
"""
import json
from typing import Optional

from pleasant_loggers import get_logger

from backend.ai_modules.clients.anthropic_client import AnthropicClient
from backend.ai_modules.csv_normalization_service.normalization_plan import AmountTransform, CategoryMapping, NormalizationPlan
from backend.database_modules.models.transactions import TransactionsTable
from backend.utils.analysis_utils import PrimaryCategories

logger = get_logger(__name__)

# Schema fields the AI can map CSV columns to
REQUIRED_SCHEMA_FIELDS = [
    TransactionsTable.authorized_date.name,
    TransactionsTable.description.name,
    TransactionsTable.primary_category.name,
    TransactionsTable.amount.name,
]
OPTIONAL_SCHEMA_FIELDS = [
    TransactionsTable.posted_date.name,
    TransactionsTable.status.name,
    TransactionsTable.account_name.name,
    TransactionsTable.detailed_category.name,
    TransactionsTable.notes.name,
    TransactionsTable.tags.name,
]
ALL_SCHEMA_FIELDS = REQUIRED_SCHEMA_FIELDS + OPTIONAL_SCHEMA_FIELDS

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
            "column_map_reasoning": {
                "type": "string",
                "description": (
                    "Brief explanation of how you mapped the CSV columns to Budgy schema fields. "
                    "Mention any ambiguous or unusual mappings."
                ),
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
            "category_map_reasoning": {
                "type": "string",
                "description": (
                    "Brief explanation of how you mapped raw category values to Budgy categories. "
                    "Mention any categories that were ambiguous or mapped broadly."
                ),
            },
            "amount_transform": {
                "type": "string",
                "enum": ["expense_negative", "expense_positive", "debit_credit"],
                "description": (
                    "How to interpret amount values in this CSV. "
                    "'expense_negative': expenses are negative numbers, income is positive — standard convention, no change needed. "
                    "'expense_positive': expenses are positive numbers, income is negative — all values will be negated on import. "
                    "'debit_credit': amounts are split across separate debit and credit columns. "
                    "Check BOTH expense and income rows to confirm the sign convention. "
                    "If only one transaction type is present, infer from those values and note the ambiguity in amount_transform_reasoning."
                ),
            },
            "amount_transform_reasoning": {
                "type": "string",
                "description": (
                    "Explain why you chose this sign convention. "
                    "Describe what you observed in the sample values (e.g. expense sign, income sign, column names). "
                    "Note any ambiguity if only one transaction type was present."
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
                "description": (
                    "File-level structural errors and unresolvable ambiguities only. "
                    "Do NOT use this for informational notes about mappings — use the reasoning fields instead. "
                    "Examples: missing required columns entirely, file appears malformed, duplicate headers."
                ),
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
            "column_map_reasoning",
            "category_map",
            "category_map_reasoning",
            "amount_transform",
            "amount_transform_reasoning",
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
                "- When in doubt, if there is only one column with date like values, map it to 'authorized_date' even if the header is unclear."
                "'posted_date' refers to when the transaction was posted to the account, which is often different from the authorized date for credit card transactions.\n"  
                "CATEGORY MAPPING:\n"
                "- Map raw category strings to the most specific valid primary+detailed category pair.\n"
                "- Only include a value in category_map if it is clearly a spending or income category "
                "(e.g. 'Groceries', 'Gas Station', 'Salary'). Do NOT map account names, bank names, "
                "card names, institution identifiers, or any string that is not a transaction category — "
                "simply omit those values from category_map entirely.\n"
                "- For amount sign convention: check BOTH expense and income transactions. "
                "If expenses are negative numbers and income is positive → use 'expense_negative'. "
                "If expenses are positive numbers and income is negative → use 'expense_positive'. "
                "If only one type of transaction is present, infer from the sign of those values "
                "and note the ambiguity in amount_transform_reasoning.\n"
                "- List any unmappable required fields in unmapped_required_columns.\n"
                "- Use issues ONLY for file-level structural errors, not informational notes.\n"
                "- Be conservative: when in doubt, prefer null over a wrong mapping.\n"
                "- Always provide reasoning for column mappings, category mappings, and the amount transform."
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


class CSVNormalizationService(AnthropicClient):
    """
    AI service for CSV column/category normalization.

    Inherits AnthropicClient for provider access. Owns the normalization
    prompt and tool schema; delegates the actual API call to complete_with_tool().
    """

    def plan_csv(
        self,
        headers: list[str],
        unique_categories: list[str],
        sample_amount_values: dict[str, list[float]] | None = None,
    ) -> NormalizationPlan:
        user_parts = [
            f"CSV headers: {json.dumps(headers)}",
            f"Unique category values found in the CSV: {json.dumps(unique_categories)}",
        ]
        if sample_amount_values:
            user_parts.append(
                f"Sample numeric values per column (use for sign convention detection): "
                f"{json.dumps(sample_amount_values)}"
            )

        logger.info(
            "Planning CSV normalization (%d headers, %d categories)",
            len(headers),
            len(unique_categories),
        )

        raw = self.complete_with_tool(
            system_prompt=_build_system_prompt(),
            messages=[{"role": "user", "content": "\n".join(user_parts)}],
            tool_schema=_NORMALIZATION_TOOL,
        )

        column_map: dict[str, Optional[str]] = raw.get("column_map", {})
        category_map = {
            k: CategoryMapping(primary=v["primary"], detailed=v["detailed"])
            for k, v in raw.get("category_map", {}).items()
        }

        logger.info(
            "Plan received: %d column mappings, %d category mappings",
            len(column_map),
            len(category_map),
        )

        return NormalizationPlan(
            column_map=column_map,
            category_map=category_map,
            amount_transform=AmountTransform(raw.get("amount_transform", "expense_negative")),
            debit_column=raw.get("debit_column"),
            credit_column=raw.get("credit_column"),
            issues=raw.get("issues", []),
            unmapped_required_columns=raw.get("unmapped_required_columns", []),
            column_map_reasoning=raw.get("column_map_reasoning"),
            category_map_reasoning=raw.get("category_map_reasoning"),
            amount_transform_reasoning=raw.get("amount_transform_reasoning"),
        )
