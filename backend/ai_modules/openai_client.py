#!python3
"""
backend.ai_modules.openai_client
OpenAI implementation of AIClient — not yet implemented.
"""
from backend.ai_modules.ai_client_base import AIClient


class OpenAIClient(AIClient):
    """Skeleton — OpenAI provider not yet implemented."""

    def complete_with_tool(
        self,
        system_prompt: list[dict],
        messages: list[dict],
        tool_schema: dict,
        max_tokens: int = 2048,
    ) -> dict:
        raise NotImplementedError("OpenAI provider is not yet implemented.")
