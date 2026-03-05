from __future__ import annotations

from typing import Any

import structlog

from app.engine.handlers.base import register_handler
from app.models.workflow_node import NodeType
from app.services.llm_gateway import llm_gateway

logger = structlog.get_logger()


@register_handler(NodeType.CRITIC_REVIEW)
class CriticReviewHandler:
    async def execute(
        self,
        node_config: dict | None,
        input_data: dict[str, Any],
        user_feedback: str | None = None,
    ) -> dict[str, Any]:
        config = node_config or {}
        max_cycles = config.get("max_cycles", 2)

        # Get the document to review from upstream
        document = ""
        for key, data in input_data.items():
            if isinstance(data, dict) and "document" in data:
                document = data["document"]
                break

        if not document:
            return {
                "verdict": "fail",
                "feedback": "No document provided for review.",
                "score": 0,
            }

        prompt = f"""You are a quality reviewer for business documents. \
Review the following document critically.

## Document to Review
{document}

## Evaluation Criteria
1. Completeness: Are all required sections present?
2. Accuracy: Are claims supported by data?
3. Clarity: Is the document clear and well-structured?
4. Actionability: Does it provide actionable insights?
5. Consistency: Are there any contradictions?

Provide:
- A verdict: "pass" or "fail"
- A score from 1-10
- Specific feedback on what to improve
- A summary of strengths

Format your response as structured analysis.
"""

        messages = [
            {"role": "system", "content": "You are a meticulous business document reviewer."},
            {"role": "user", "content": prompt},
        ]

        review = await llm_gateway.complete(messages)

        # Parse verdict from review (simple heuristic)
        verdict = "pass" if "pass" in review.lower()[:100] else "fail"
        score_estimate = 7.0 if verdict == "pass" else 4.0

        return {
            "verdict": verdict,
            "feedback": review,
            "score": score_estimate,
            "max_cycles": max_cycles,
        }
