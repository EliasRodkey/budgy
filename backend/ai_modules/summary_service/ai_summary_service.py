#!python3
"""
backend.ai_modules.ai_summary_service
AI service for generating plain-language monthly/yearly financial summaries.
Uses tool_use structured output for a guaranteed AISummaryData shape.
"""
from datetime import datetime, timezone

from pleasant_loggers import get_logger

from backend.ai_modules.clients.ai_client_base import AIClient
from backend.api.ai.ai_models import AISummaryData
from backend.utils.summary_utils import MonthlySummaryResponse

logger = get_logger(__name__)

_SUMMARY_TOOL = {
    "name": "return_financial_summary",
    "description": (
        "Return a plain-language summary of a user's financial data for a given period. "
        "Include a concise recap, a list of anomalous spending patterns, and actionable savings suggestions."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "recap": {
                "type": "string",
                "description": (
                    "2-4 sentence plain-language recap of the period. "
                    "Mention total income, total spending, and net. "
                    "Highlight the top 1-2 spending categories. Keep it conversational."
                ),
            },
            "anomalies": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "List of unusual spending patterns. Each item is one concise sentence "
                    "(e.g. 'Food & drink is 140% of the monthly budget'). "
                    "Empty list if nothing stands out."
                ),
            },
            "suggestions": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "List of 2-4 actionable savings suggestions based on the data. "
                    "Each item is one concrete, specific suggestion."
                ),
            },
        },
        "required": ["recap", "anomalies", "suggestions"],
    },
}

_SYSTEM_PROMPT = [
    {
        "type": "text",
        "text": (
            "You are a personal finance assistant for Budgy, a budgeting app. "
            "Your job is to generate clear, helpful summaries of a user's spending data. "
            "Rules:\n"
            "- Be specific: reference actual category names and dollar amounts from the data.\n"
            "- Anomalies should be data-driven (over budget, unusually high spend, etc.).\n"
            "- Suggestions should be actionable and tied to what you observe in the data.\n"
            "- Tone: friendly and direct, not preachy.\n"
            "- Amounts are in USD. Format as '$X' or '$X,XXX' as appropriate.\n"
            "- Non-spending categories (Income, Transfers, Investments) are context — "
            "do not flag them as anomalies or suggest reducing them."
        ),
        "cache_control": {"type": "ephemeral"},
    }
]

_NON_SPENDING = {"Income", "Transfers", "Investments"}


def _build_user_message(summary: MonthlySummaryResponse) -> str:
    """
    Build the user message from a MonthlySummaryResponse using only the
    fields that are meaningful for a language-model summary (no IDs or counts).
    """
    lines = [
        f"Period: {summary.month}",
        f"Total income: ${summary.total_income:,.2f}",
        f"Total expenses: ${summary.total_expenses:,.2f}",
        f"Net: ${summary.net:,.2f}",
        "",
        "Spending by category:",
    ]
    for cat in summary.by_category:
        if cat.amount == 0:
            continue
        line = f"  {cat.category_name}: ${cat.amount:,.2f}"
        if cat.monthly_limit is not None and cat.percent_of_limit is not None:
            line += f" (budget: ${cat.monthly_limit:,.2f}, {cat.percent_of_limit:.0f}%)"
            if cat.is_over_budget:
                line += " ⚠ over budget"
        lines.append(line)
    return "\n".join(lines)


class AISummaryService:
    """
    Generates plain-language financial summaries using tool_use structured output.

    Args:
        client: Any AIClient implementation (AnthropicClient, future OpenAIClient, etc.).
    """

    def __init__(self, client: AIClient):
        self._client = client

    def summarize(self, summary: MonthlySummaryResponse) -> AISummaryData:
        """
        Generate an AISummaryData for the given MonthlySummaryResponse.

        Raises:
            AIAuthError, AICreditsError, AIRateLimitError, AITimeoutError, AIProviderError
        """
        user_message = _build_user_message(summary)
        logger.info(f"Generating AI summary for period '{summary.month}'")

        raw = self._client.complete_with_tool(
            system_prompt=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
            tool_schema=_SUMMARY_TOOL,
        )

        return AISummaryData(
            generated_at=datetime.now(tz=timezone.utc),
            recap=raw.get("recap", ""),
            anomalies=raw.get("anomalies", []),
            suggestions=raw.get("suggestions", []),
        )
