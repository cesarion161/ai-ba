"""Pre-fill ask_user node answers from chat requirements summary."""

from __future__ import annotations

import json
import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow_node import NodeType, WorkflowNode
from app.services.llm_gateway import llm_gateway

logger = structlog.get_logger()


async def prefill_ask_user_answers(
    session: AsyncSession,
    project_id: uuid.UUID,
    requirements_summary: str,
    nodes: list[WorkflowNode],
) -> None:
    """Use LLM to pre-fill answers for ask_user nodes based on requirements summary.

    Nodes stay in AWAITING_INPUT so users can review/edit before submitting.
    Fails silently — if the LLM call fails, nodes just remain empty.
    """
    ask_user_nodes = [n for n in nodes if n.node_type == NodeType.ASK_USER]
    if not ask_user_nodes:
        return

    # Build question map: slug -> list of questions
    question_map: dict[str, list[str]] = {}
    for node in ask_user_nodes:
        questions = (node.config or {}).get("questions", [])
        if questions:
            question_map[node.slug] = questions

    if not question_map:
        return

    try:
        prompt = _build_prompt(requirements_summary, question_map)
        response = await llm_gateway.complete(
            messages=[{"role": "user", "content": prompt}],
            task_type="analysis",
        )
        answers_by_slug = _parse_response(response, question_map)

        for node in ask_user_nodes:
            slug_answers = answers_by_slug.get(node.slug)
            if slug_answers:
                questions = (node.config or {}).get("questions", [])
                node.output_data = {
                    "answers": slug_answers,
                    "questions": questions,
                    "prefilled": True,
                }

        await session.flush()
        logger.info(
            "prefill_answers_complete",
            project_id=str(project_id),
            prefilled_count=len(answers_by_slug),
        )
    except Exception:
        logger.exception("prefill_answers_failed", project_id=str(project_id))


def _build_prompt(requirements_summary: str, question_map: dict[str, list[str]]) -> str:
    questions_block = json.dumps(question_map, indent=2)
    return f"""You are helping pre-fill a business analysis questionnaire based on information already gathered from the user.

## Requirements Summary (from user conversation)
{requirements_summary}

## Questions to Answer
The following JSON maps node slugs to lists of questions. Answer each question using ONLY information from the requirements summary above. If the summary doesn't contain enough information to answer a question, use an empty string "".

{questions_block}

## Instructions
- Return a JSON object where keys are node slugs and values are objects mapping each question to its answer.
- Use the exact question text as keys in the answer objects.
- Keep answers concise but informative (1-3 sentences).
- Only use information from the requirements summary — do not invent or assume facts.
- Return ONLY valid JSON, no markdown fences or extra text.

Example format:
{{"node_slug": {{"Question text here?": "Answer based on summary"}}}}"""


def _parse_response(
    response: str, question_map: dict[str, list[str]]
) -> dict[str, dict[str, str]]:
    """Parse LLM response into answers keyed by slug."""
    # Strip markdown fences if present
    text = response.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        return {}

    # Validate structure: only keep slugs we know about
    result: dict[str, dict[str, str]] = {}
    for slug, answers in parsed.items():
        if slug in question_map and isinstance(answers, dict):
            result[slug] = {k: str(v) for k, v in answers.items()}
    return result
