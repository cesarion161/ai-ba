"""Workflow error classification for retry decisions."""

from __future__ import annotations


class NonRetryableError(Exception):
    """Permanent failure — retrying will not help.

    Examples: billing/quota exhausted, content policy violation,
    context length exceeded.
    """


# Patterns that mean "don't retry this node at all" — the problem is with the
# request itself, not the provider.  Checked case-insensitively.
NON_RETRYABLE_PATTERNS = (
    "billing",
    "quota",
    "insufficient_quota",
    "account_deactivated",
    "content_policy",
    "content_filter",
    "context_length_exceeded",
    "invalid_request",
)

# Patterns that mean "skip to the next fallback model" — the problem is with
# this specific provider/key, but another provider may work.
SKIP_MODEL_PATTERNS = (
    "authentication",
    "auth_error",
    "invalid_api_key",
    "invalid api key",
    "permission denied",
    "model_not_found",
)


def is_non_retryable(error: Exception) -> bool:
    """Check if an error is permanent and should not be retried at any level."""
    if isinstance(error, NonRetryableError):
        return True
    error_str = str(error).lower()
    return any(p in error_str for p in NON_RETRYABLE_PATTERNS)


def should_skip_model(error: Exception) -> bool:
    """Check if the error is model/provider-specific — try next fallback."""
    error_str = str(error).lower()
    return any(p in error_str for p in SKIP_MODEL_PATTERNS)
