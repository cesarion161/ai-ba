"""Conversational agent for gathering business requirements."""

from __future__ import annotations

import json

import structlog

from app.services.llm_gateway import llm_gateway
from app.services.prompt_engine import prompt_engine

logger = structlog.get_logger()


class InitialAnalysisAgent:
    async def process_message(self, history: list[dict[str, str]], user_message: str) -> str:
        """Generate a response to continue the requirements conversation."""
        try:
            system_prompt = prompt_engine.render("chat/initial_analysis")
        except Exception:
            system_prompt = self._default_system_prompt()

        messages = [{"role": "system", "content": system_prompt}] + history

        response = await llm_gateway.complete(
            messages=messages,
            task_type="chat",
        )
        return response

    async def is_requirements_complete(self, history: list[dict[str, str]]) -> dict:
        """Check if we have enough info to proceed."""
        if len(history) < 4:
            return {"complete": False, "summary": "Need more conversation"}

        try:
            check_prompt = prompt_engine.render("chat/requirements_check")
        except Exception:
            check_prompt = self._default_requirements_check_prompt()

        messages = [
            {"role": "system", "content": check_prompt},
            {
                "role": "user",
                "content": (
                    "Based on the following conversation, determine if we have enough "
                    "information to generate a business analysis. Respond with JSON: "
                    '{"complete": true/false, "summary": "brief summary of what we know"}\n\n'
                    + "\n".join(f"{m['role']}: {m['content']}" for m in history)
                ),
            },
        ]

        response = await llm_gateway.complete(messages=messages, task_type="analysis")

        try:
            # Try to parse JSON from response
            json_str = response.strip()
            if "```" in json_str:
                json_str = json_str.split("```")[1].strip()
                if json_str.startswith("json"):
                    json_str = json_str[4:].strip()
            result = json.loads(json_str)
            return {"complete": bool(result.get("complete")), "summary": result.get("summary", "")}
        except (json.JSONDecodeError, KeyError):
            logger.warning("Failed to parse requirements check response", response=response)
            return {"complete": False, "summary": "Could not determine completeness"}

    async def get_recommended_doc_types(
        self, history: list[dict[str, str]], all_doc_types: list[dict]
    ) -> list[str]:
        """Recommend which document types are relevant based on the conversation."""
        doc_list = "\n".join(
            f"- {dt['key']}: {dt['label']} - {dt['description']}" for dt in all_doc_types
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a business analyst. Based on the conversation, "
                    "recommend which document types should be generated. "
                    "Respond with a JSON array of document type keys."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Available document types:\n{doc_list}\n\n"
                    "Conversation:\n"
                    + "\n".join(f"{m['role']}: {m['content']}" for m in history)
                    + "\n\nReturn a JSON array of recommended doc type keys."
                ),
            },
        ]

        response = await llm_gateway.complete(messages=messages, task_type="analysis")

        try:
            json_str = response.strip()
            if "```" in json_str:
                json_str = json_str.split("```")[1].strip()
                if json_str.startswith("json"):
                    json_str = json_str[4:].strip()
            result: list[str] = json.loads(json_str)
            return result
        except (json.JSONDecodeError, KeyError):
            return [str(dt["key"]) for dt in all_doc_types]

    @staticmethod
    def _default_system_prompt() -> str:
        return """You are an AI business analyst helping a user define their business project.

Your goal is to gather enough information to generate comprehensive business analysis documents.

Ask focused questions about:
1. The business idea / product / service
2. Target market and customer segments
3. Competition and market landscape
4. Revenue model and pricing strategy
5. Technical requirements (if applicable)
6. Timeline and budget constraints

Be conversational and friendly. Ask 1-2 questions at a time. Build on previous answers.
When you have a clear picture, let the user know you're ready to proceed."""

    @staticmethod
    def _default_requirements_check_prompt() -> str:
        return """\
You analyze conversations to determine if enough \
business requirements have been gathered.

Requirements are considered complete when we have clear information about:
- What the business/product is
- Who the target customers are
- Basic understanding of the market
- Revenue/business model direction

Respond ONLY with valid JSON: {"complete": true/false, "summary": "brief summary"}"""
