#!python3
"""
backend.ai_modules.anthropic_client
Anthropic SDK implementation of AIClient.

Catches Anthropic-specific exceptions and re-raises as provider-agnostic
AIError subclasses so routers never import SDK exception types.
"""
import os
from typing import Any

import anthropic
from pleasant_loggers import get_logger

from backend.ai_modules.ai_client_base import AIClient
from backend.ai_modules.ai_errors import (
    AIAuthError,
    AICreditsError,
    AIProviderError,
    AIRateLimitError,
    AITimeoutError,
)

logger = get_logger(__name__)

_DEFAULT_MODEL = "claude-haiku-4-5-20251001"


class AnthropicClient(AIClient):
    """
    Anthropic SDK implementation of AIClient.

    Args:
        model: Model ID. Resolved from constructor → AI_MODEL env var → default.
               Pass a user's preferred model here for per-user model selection.
        api_key: Anthropic API key. Defaults to ANTHROPIC_API_KEY env var.
    """

    def __init__(self, model: str | None = None, api_key: str | None = None):
        self.model = model or os.environ.get("AI_MODEL", _DEFAULT_MODEL)
        self._client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )

    def complete_with_tool(
        self,
        system_prompt: list[dict],
        messages: list[dict],
        tool_schema: dict,
        max_tokens: int = 2048,
    ) -> dict:
        logger.info(f"Calling Anthropic ({self.model}) with tool '{tool_schema.get('name')}'")
        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                tools=[tool_schema],
                tool_choice={"type": "tool", "name": tool_schema["name"]},
                messages=messages,
            )
        except anthropic.AuthenticationError as exc:
            raise AIAuthError(str(exc)) from exc
        except anthropic.PermissionDeniedError as exc:
            raise AIAuthError(str(exc)) from exc
        except anthropic.RateLimitError as exc:
            raise AIRateLimitError(str(exc)) from exc
        except anthropic.APITimeoutError as exc:
            raise AITimeoutError(str(exc)) from exc
        except anthropic.BadRequestError as exc:
            if "credit balance is too low" in str(exc).lower():
                raise AICreditsError(str(exc)) from exc
            raise AIProviderError(str(exc)) from exc
        except anthropic.APIError as exc:
            raise AIProviderError(str(exc)) from exc

        tool_block = next(b for b in response.content if b.type == "tool_use")
        return tool_block.input
