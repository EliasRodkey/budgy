#!python3
"""
backend.ai_modules.ai_errors
Custom exception types for AI provider errors. Routers catch these instead of
SDK-specific exceptions, keeping provider details out of endpoint logic.
"""


class AIError(Exception):
    """Base class for all AI provider errors."""


class AIAuthError(AIError):
    """API key missing, invalid, or lacking permissions. Maps to HTTP 503."""


class AICreditsError(AIError):
    """Account has insufficient credits. Maps to HTTP 402."""


class AIRateLimitError(AIError):
    """Provider rate limit exceeded. Maps to HTTP 429."""


class AITimeoutError(AIError):
    """Request timed out waiting for the model. Maps to HTTP 504."""


class AIProviderError(AIError):
    """Catch-all for other upstream provider errors. Maps to HTTP 502."""
