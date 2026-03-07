from __future__ import annotations

from typing import Any

import structlog

from app.engine.handlers.base import register_handler
from app.models.workflow_node import NodeType
from app.services.llm_gateway import llm_gateway
from app.services.prompt_engine import prompt_engine
from app.services.sandbox import python_sandbox

logger = structlog.get_logger()


@register_handler(NodeType.CALCULATE)
class CalculateHandler:
    async def execute(
        self,
        node_config: dict | None,
        input_data: dict[str, Any],
        user_feedback: str | None = None,
    ) -> dict[str, Any]:
        config = node_config or {}
        calculation = config.get("calculation", "general")

        # Gather upstream research data
        research_data = ""
        business_context = input_data.pop("_requirements_summary", "")
        for key, data in input_data.items():
            if isinstance(data, dict):
                if "summary" in data:
                    research_data += data["summary"] + "\n\n"

        # Use LLM to generate Python calculation code
        code_prompt = (
            "Write a Python script that calculates TAM/SAM/SOM based on the following data. "
            "Print the results as structured output. Use only standard library modules.\n\n"
            f"Research data:\n{research_data[:2000]}\n\n"
            f"Business context:\n{business_context[:1000]}\n\n"
            "Output format: print each metric with its value."
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a data analyst. Output ONLY valid Python code, no markdown fences."
                ),
            },
            {"role": "user", "content": code_prompt},
        ]

        generated_code = await llm_gateway.complete(messages, temperature=0.1)

        # Strip markdown fences if present
        code = generated_code.strip()
        if code.startswith("```"):
            lines = code.split("\n")
            code = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        # Execute in sandbox
        sandbox_result = await python_sandbox.execute(code, timeout=60)

        if sandbox_result.success:
            logger.info("sandbox_calculation_success", calculation=calculation)
        else:
            logger.warning(
                "sandbox_calculation_failed",
                error=sandbox_result.error,
                falling_back="llm",
            )

        # Also generate LLM narrative analysis
        try:
            narrative_prompt = prompt_engine.render(
                "market_research/market_sizing",
                research_data=research_data,
                business_context=business_context,
            )
        except Exception:
            narrative_prompt = (
                f"Calculate TAM/SAM/SOM based on:\n"
                f"Research: {research_data[:1000]}\n"
                f"Context: {business_context[:500]}"
            )

        messages = [
            {"role": "system", "content": "You are a market sizing analyst."},
            {"role": "user", "content": narrative_prompt},
        ]

        narrative = await llm_gateway.complete(messages)

        return {
            "result": narrative,
            "calculation_type": calculation,
            "sandbox_output": sandbox_result.stdout if sandbox_result.success else None,
            "sandbox_error": sandbox_result.error,
            "charts": sandbox_result.charts,
            "figures": {},
        }
