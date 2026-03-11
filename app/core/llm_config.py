"""Model routing configuration — maps task types to preferred models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModelConfig:
    primary: str
    fallbacks: list[str] = field(default_factory=list)
    temperature: float = 0.7
    max_tokens: int = 4096


# Task-specific model routing
# Complex nodes use gpt-5.4-pro (best reasoning) with gpt-5.4 fallback
# Less complex nodes use gpt-4.1 as the all-around workhorse
MODEL_ROUTING: dict[str, ModelConfig] = {
    "research": ModelConfig(
        primary="gpt-5.4-pro",
        fallbacks=["gpt-5.4", "gpt-4.1"],
        temperature=0.3,
        max_tokens=128000,
    ),
    "calculate": ModelConfig(
        primary="gpt-4.1",
        fallbacks=["gpt-5.4"],
        temperature=0.1,
        max_tokens=32768,
    ),
    "generate_document": ModelConfig(
        primary="gpt-5.4-pro",
        fallbacks=["gpt-5.4", "gpt-4.1"],
        temperature=0.4,
        max_tokens=128000,
    ),
    "critic_review": ModelConfig(
        primary="gpt-5.4-pro",
        fallbacks=["gpt-5.4", "gpt-4.1"],
        temperature=0.3,
        max_tokens=128000,
    ),
    "ask_user": ModelConfig(
        primary="gpt-4.1",
        fallbacks=["gpt-5.4"],
        temperature=0.5,
        max_tokens=32768,
    ),
    "densify": ModelConfig(
        primary="gpt-5.4-pro",
        fallbacks=["gpt-5.4", "gpt-4.1"],
        temperature=0.2,
        max_tokens=128000,
    ),
    "generate_backlog": ModelConfig(
        primary="gpt-5.4-pro",
        fallbacks=["gpt-5.4", "gpt-4.1"],
        temperature=0.2,
        max_tokens=128000,
    ),
    "format_export": ModelConfig(
        primary="gpt-4.1",
        fallbacks=["gpt-5.4"],
        temperature=0.1,
        max_tokens=32768,
    ),
    "chat": ModelConfig(
        primary="gpt-4.1",
        fallbacks=["gpt-5.4"],
        temperature=0.7,
        max_tokens=32768,
    ),
    "analysis": ModelConfig(
        primary="gpt-4.1",
        fallbacks=["gpt-5.4"],
        temperature=0.2,
        max_tokens=32768,
    ),
}


def get_model_config(task_type: str) -> ModelConfig:
    return MODEL_ROUTING.get(
        task_type,
        ModelConfig(primary="gpt-4.1", fallbacks=["gpt-5.4"]),
    )
