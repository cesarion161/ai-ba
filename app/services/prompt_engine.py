from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class PromptEngine:
    def __init__(self, prompts_dir: Path = PROMPTS_DIR) -> None:
        self.env = Environment(
            loader=FileSystemLoader(str(prompts_dir)),
            autoescape=select_autoescape([]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, template_key: str, **context: Any) -> str:
        template = self.env.get_template(f"{template_key}.jinja2")
        return template.render(**context)


prompt_engine = PromptEngine()
