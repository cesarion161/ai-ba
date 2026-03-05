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
MODEL_ROUTING: dict[str, ModelConfig] = {
    "research": ModelConfig(
        primary="claude-sonnet-4-20250514",
        fallbacks=["gpt-4o", "gemini/gemini-2.0-flash"],
        temperature=0.3,
        max_tokens=4096,
    ),
    "calculate": ModelConfig(
        primary="claude-sonnet-4-20250514",
        fallbacks=["gpt-4o"],
        temperature=0.1,
        max_tokens=4096,
    ),
    "generate_document": ModelConfig(
        primary="claude-sonnet-4-20250514",
        fallbacks=["gpt-4o"],
        temperature=0.7,
        max_tokens=8192,
    ),
    "critic_review": ModelConfig(
        primary="claude-sonnet-4-20250514",
        fallbacks=["gpt-4o"],
        temperature=0.3,
        max_tokens=4096,
    ),
    "ask_user": ModelConfig(
        primary="claude-sonnet-4-20250514",
        fallbacks=["gpt-4o-mini"],
        temperature=0.5,
        max_tokens=2048,
    ),
    "densify": ModelConfig(
        primary="claude-sonnet-4-20250514",
        fallbacks=["gpt-4o"],
        temperature=0.2,
        max_tokens=8192,
    ),
    "format_export": ModelConfig(
        primary="claude-sonnet-4-20250514",
        fallbacks=["gpt-4o-mini"],
        temperature=0.1,
        max_tokens=2048,
    ),
}


def get_model_config(task_type: str) -> ModelConfig:
    return MODEL_ROUTING.get(
        task_type,
        ModelConfig(primary="claude-sonnet-4-20250514", fallbacks=["gpt-4o"]),
    )
