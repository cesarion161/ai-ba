from __future__ import annotations

from typing import Any

import structlog

from app.engine.handlers.base import register_handler
from app.models.workflow_node import NodeType
from app.services.llm_gateway import llm_gateway
from app.services.prompt_engine import prompt_engine

logger = structlog.get_logger()

# System messages tailored by document branch
SYSTEM_MESSAGES: dict[str, str] = {
    "technical_architecture": (
        "You are a principal software architect and system design expert with 15+ years "
        "of experience building production systems at scale. You have deep expertise in "
        "distributed systems, cloud-native architectures, microservices, event-driven "
        "design, database internals, caching strategies, and infrastructure cost "
        "optimization. You think in terms of trade-offs, failure modes, and operational "
        "realities — not textbook ideals. Your documents are detailed enough that a "
        "senior engineering team can start implementation immediately."
    ),
    "execution_planning": (
        "You are a senior technical program manager and delivery lead with 15+ years "
        "of experience shipping complex software products. You create actionable, "
        "realistic execution plans grounded in engineering effort estimates, dependency "
        "analysis, and risk mitigation. Your plans are detailed enough for sprint "
        "planning and resource allocation."
    ),
    "product_strategy": (
        "You are a senior product strategist with deep experience in product-led growth, "
        "go-to-market strategy, and competitive positioning. You create data-driven "
        "roadmaps with clear prioritization frameworks and success metrics."
    ),
    "ux_requirements": (
        "You are a senior UX architect and requirements analyst with deep experience "
        "in user-centered design, information architecture, and accessibility. You "
        "create comprehensive user stories with clear acceptance criteria that "
        "engineering teams can implement without ambiguity."
    ),
    "market_research": (
        "You are a business strategy consultant with expertise in market analysis, "
        "competitive intelligence, and business model design."
    ),
    "business_requirements": (
        "You are a senior business analyst with 15+ years of experience in requirements "
        "engineering, BABOK methodology, and business process analysis. You create "
        "precise, testable requirements that prevent engineering from filling in "
        "critical business logic themselves. You focus on the 'what' and 'why', "
        "not the 'how'."
    ),
    "delivery": (
        "You are a senior delivery architect with deep experience in API design, "
        "data modeling, test strategy, and requirements traceability. You create "
        "execution-grade specifications that engineering teams can implement without "
        "ambiguity. Every specification must be precise enough that two independent "
        "teams would build compatible systems from it."
    ),
}

# Template path mapping: branch → {template_name → template_path}
# This resolves the correct subdirectory for each branch.
BRANCH_TEMPLATE_DIRS: dict[str, str] = {
    "technical_architecture": "technical_architecture",
    "execution_planning": "execution_planning",
    "product_strategy": "product_strategy",
    "ux_requirements": "ux_requirements",
    "market_research": "market_research",
    "business_requirements": "business_requirements",
    "delivery": "delivery",
}


@register_handler(NodeType.GENERATE_DOCUMENT)
class GenerateDocumentHandler:
    async def execute(
        self,
        node_config: dict | None,
        input_data: dict[str, Any],
        user_feedback: str | None = None,
    ) -> dict[str, Any]:
        config = node_config or {}
        template_name = config.get("template", "generic")
        branch = config.get("branch", "market_research")

        # Gather all upstream outputs
        requirements = input_data.pop("_requirements_summary", "")
        context_parts: dict[str, str] = {}
        for key, data in input_data.items():
            if isinstance(data, dict):
                if "summary" in data:
                    context_parts[key] = data["summary"]
                elif "result" in data:
                    context_parts[key] = data["result"]
                elif "document" in data:
                    context_parts[key] = data["document"]

        # Resolve template path using branch directory
        template_dir = BRANCH_TEMPLATE_DIRS.get(branch, "market_research")
        template_path = f"{template_dir}/{template_name}"

        # Build flexible context: pass all upstream data + requirements + feedback
        # so templates can pick what they need via Jinja2 variable names
        template_context = {
            # Common fields every template may use
            "requirements_summary": requirements,
            "product_requirements": requirements,
            "product_overview": requirements,
            "product_description": requirements,
            "user_feedback": user_feedback,
            # Pass all upstream outputs by their node key
            **context_parts,
            # Also map common expected variable names to upstream data
            "research_summary": context_parts.get("web_search", ""),
            "competitor_analysis": context_parts.get("competitor_analysis", ""),
            "market_sizing": context_parts.get("market_sizing", ""),
            "tech_research": context_parts.get("tech_stack_research", ""),
            "tech_expertise": context_parts.get("tech_stack_research", ""),
            "scalability": context_parts.get("tech_stack_research", ""),
            "integrations": context_parts.get("tech_stack_research", ""),
            "feature_research": context_parts.get("feature_landscape_research", ""),
            "pricing_research": context_parts.get("pricing_model_research", ""),
            "ux_research": context_parts.get("ux_best_practices_research", ""),
            "user_personas": context_parts.get("ux_best_practices_research", ""),
            "user_journeys": context_parts.get("ux_best_practices_research", ""),
            "platforms": requirements,
            "user_answers": requirements,
            "team_info": requirements,
            "budget": requirements,
            "timeline": requirements,
            "risks": context_parts.get("cost_estimation", ""),
            "cost_estimation": context_parts.get("cost_estimation", ""),
            "scalability_needs": requirements,
            "integration_requirements": requirements,
            "team_expertise": requirements,
            # Feasibility & business requirements context
            "lean_canvas": context_parts.get("lean_canvas", ""),
            "feasibility_assessment": context_parts.get("feasibility_assessment", ""),
            "business_rules": context_parts.get("business_rules", ""),
            "process_model": context_parts.get("process_model", ""),
            "brd": context_parts.get("brd", ""),
            # Delivery context
            "architecture_doc": context_parts.get("architecture_doc", ""),
            "user_stories": context_parts.get("user_stories", ""),
            "product_roadmap": context_parts.get("product_roadmap", ""),
            "execution_plan": context_parts.get("execution_plan", ""),
            "qa_strategy": context_parts.get("qa_strategy", ""),
            "nfr_context": context_parts.get("architecture_doc", ""),
            "product_backlog": context_parts.get("product_backlog", ""),
        }

        # Try to render the branch-specific template
        try:
            prompt = prompt_engine.render(template_path, **template_context)
        except Exception:
            logger.warning(
                "template_not_found",
                template_path=template_path,
                falling_back_to="generic",
            )
            # Fall back to generic prompt with all context
            prompt = f"Generate a comprehensive {template_name.replace('_', ' ')} document.\n\n"
            if requirements:
                prompt += f"## Business Requirements\n{requirements}\n\n"
            for key, val in context_parts.items():
                prompt += f"## {key.replace('_', ' ').title()}\n{val}\n\n"
            if user_feedback:
                prompt += f"## Revision Instructions\n{user_feedback}\n\n"

        system_message = SYSTEM_MESSAGES.get(branch, SYSTEM_MESSAGES["market_research"])

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ]

        document = await llm_gateway.complete(
            messages,
            task_type="generate_document",
        )

        return {
            "document": document,
            "title": template_name.replace("_", " ").title(),
            "format": "markdown",
        }
