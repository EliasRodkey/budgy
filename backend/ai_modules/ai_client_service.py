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
                "- Map column headers to the closest matching schema field. Use null if no reasonable match exists.\n"
                "- Map category strings to the most specific valid primary+detailed category pair.\n"
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
    ) -> NormalizationPlan:
        """
        Analyze CSV headers and unique category values, return a NormalizationPlan.

        Args:
            headers: Raw column header strings from the CSV.
            unique_categories: Unique values found in any category-like column.

        Returns:
            NormalizationPlan with column_map, category_map, amount_transform, and reasoning.
        """
        user_text = (
            f"CSV headers: {json.dumps(headers)}\n"
            f"Unique category values found in the CSV: {json.dumps(unique_categories)}"
        )

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
            amount_transform=AmountTransform(raw.get("amount_transform", "expense_negative")),
            debit_column=raw.get("debit_column"),
            credit_column=raw.get("credit_column"),
            issues=raw.get("issues", []),
            unmapped_required_columns=raw.get("unmapped_required_columns", []),
            column_map_reasoning=raw.get("column_map_reasoning"),
            category_map_reasoning=raw.get("category_map_reasoning"),
            amount_transform_reasoning=raw.get("amount_transform_reasoning"),
        )
