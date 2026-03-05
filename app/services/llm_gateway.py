from __future__ import annotations

from typing import Any, cast

import structlog
from litellm import acompletion

from app.core.config import get_settings
from app.core.llm_config import get_model_config

logger = structlog.get_logger()


class LLMGateway:
    def __init__(self) -> None:
        self.settings = get_settings()

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

        last_error: Exception | None = None
        for m in models_to_try:
            try:
                response = await acompletion(
                    model=m,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                content = response.choices[0].message.content
                logger.info(
                    "llm_completion",
                    model=m,
                    task_type=task_type,
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens,
                )
                return cast(str, content)
            except Exception as e:
                logger.warning("llm_fallback", model=m, error=str(e))
                last_error = e
                continue

        raise RuntimeError(f"All models failed. Last error: {last_error}")

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
