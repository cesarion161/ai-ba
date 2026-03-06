from __future__ import annotations

import asyncio
from typing import Any, cast

import structlog
from litellm import acompletion

from app.core.config import get_settings
from app.core.llm_config import get_model_config

logger = structlog.get_logger()

TRANSIENT_ERROR_STRINGS = ("rate_limit", "timeout", "connection", "429", "503", "502")
MAX_RETRIES = 3
BACKOFF_SECONDS = [1, 2, 4]


def _is_transient(error: Exception) -> bool:
    """Check if an error is transient and worth retrying."""
    error_str = str(error).lower()
    return any(s in error_str for s in TRANSIENT_ERROR_STRINGS)


class LLMGateway:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def _complete_with_retry(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        **kwargs: Any,
    ) -> str | None:
        """Try a single model with retry logic for transient errors."""
        for attempt in range(MAX_RETRIES):
            try:
                response = await acompletion(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                content = response.choices[0].message.content
                logger.info(
                    "llm_completion",
                    model=model,
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens,
                )
                return cast(str, content)
            except Exception as e:
                if _is_transient(e) and attempt < MAX_RETRIES - 1:
                    wait = BACKOFF_SECONDS[attempt]
                    logger.warning(
                        "llm_retry",
                        model=model,
                        attempt=attempt + 1,
                        wait_seconds=wait,
                        error=str(e),
                    )
                    await asyncio.sleep(wait)
                    continue
                logger.warning("llm_model_failed", model=model, error=str(e))
                return None
        return None

    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        task_type: str | None = None,
        **kwargs: Any,
    ) -> str:
        # Use task-specific model routing if task_type provided
        if task_type:
            config = get_model_config(task_type)
            model = model or config.primary
            temperature = temperature if temperature is not None else config.temperature
            max_tokens = max_tokens or config.max_tokens
            fallbacks = config.fallbacks
        else:
            model = model or self.settings.DEFAULT_MODEL
            temperature = temperature if temperature is not None else 0.7
            max_tokens = max_tokens or 4096
            fallbacks = self.settings.FALLBACK_MODELS

        models_to_try = [model] + fallbacks

        for m in models_to_try:
            result = await self._complete_with_retry(
                m, messages, temperature, max_tokens, **kwargs
            )
            if result is not None:
                return result

        raise RuntimeError("All models failed after retries")

    async def complete_structured(
        self,
        messages: list[dict[str, str]],
        response_format: dict | None = None,
        model: str | None = None,
        task_type: str | None = None,
        **kwargs: Any,
    ) -> str:
        extra = {}
        if response_format:
            extra["response_format"] = response_format
        return await self.complete(messages, model=model, task_type=task_type, **kwargs, **extra)  # type: ignore[arg-type]


llm_gateway = LLMGateway()
