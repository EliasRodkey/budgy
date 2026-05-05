#!python3
"""
backend.ai_modules.ai_client_base
Abstract base class for AI provider clients.

Each provider subclass implements the same interface so service classes
(CSVNormalizationService, AISummaryService, etc.) remain provider-agnostic.
Per-user model selection is supported via the model constructor param —
passing a user's preferred model at request time requires no service changes.
"""
from abc import ABC, abstractmethod
from typing import Any


class AIClient(ABC):
    """
    Abstract interface for AI provider clients.

    Subclasses: AnthropicClient, OpenAIClient (stub).
    """

    @abstractmethod
    def complete_with_tool(
        self,
        system_prompt: list[dict],
        messages: list[dict],
        tool_schema: dict,
        max_tokens: int = 2048,
    ) -> dict:
        """
        Call the provider with a forced tool_use response.

        Args:
            system_prompt: List of content blocks (supports cache_control).
            messages: List of user/assistant message dicts.
            tool_schema: Tool definition dict with name, description, input_schema.
            max_tokens: Maximum tokens in the response.

        Returns:
            The tool input dict from the provider's response.

        Raises:
            AIAuthError: Missing or invalid API key.
            AICreditsError: Account has no credits.
            AIRateLimitError: Rate limit exceeded.
            AITimeoutError: Request timed out.
            AIProviderError: Other upstream error.
        """
