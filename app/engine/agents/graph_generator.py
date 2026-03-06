"""Agent that composes workflow graph from templates + user preferences."""

from __future__ import annotations

import json
from collections import defaultdict

import structlog

from app.engine.templates.base import NodeTemplate, WorkflowTemplate
from app.engine.templates.registry import TEMPLATE_REGISTRY
from app.models.workflow_node import NodeType
from app.services.llm_gateway import llm_gateway

logger = structlog.get_logger()

# Map document type keys to template keys and relevant node slugs
DOC_TYPE_TO_TEMPLATE: dict[str, list[tuple[str, list[str]]]] = {
    "lean_canvas": [
        ("market_research", ["intake_questions", "web_search", "competitor_analysis", "lean_canvas", "lean_canvas_critic"]),
    ],
    "competitor_analysis": [
        ("market_research", ["intake_questions", "web_search", "competitor_analysis"]),
    ],
    "market_sizing": [
        ("market_research", ["intake_questions", "web_search", "competitor_analysis", "market_sizing"]),
    ],
    "product_roadmap": [
        ("product_strategy", ["product_questions", "feature_research", "pricing_research", "product_roadmap", "roadmap_critic"]),
    ],
    "user_stories": [
        ("ux_requirements", ["ux_questions", "ux_research", "user_stories", "stories_critic"]),
    ],
    "architecture_doc": [
        ("technical_architecture", ["tech_questions", "tech_stack_research", "architecture_doc", "architecture_critic"]),
    ],
    "execution_plan": [
        ("execution_planning", ["execution_questions", "cost_estimation", "execution_plan", "plan_critic"]),
    ],
}


class GraphGeneratorAgent:
    async def reorganize_requirements(
        self, history: list[dict[str, str]], selected_doc_types: list[str]
    ) -> str:
        """Produce a clean structured summary of requirements."""
        messages = [
            {
                "role": "system",
                "content": (
                    "Summarize the following conversation into structured business requirements. "
                    "Include: business description, target market, competition, revenue model, "
                    "and any other relevant details. Be concise but comprehensive."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Conversation:\n"
                    + "\n".join(f"{m['role']}: {m['content']}" for m in history)
                    + f"\n\nSelected document types: {', '.join(selected_doc_types)}"
                ),
            },
        ]
        return await llm_gateway.complete(messages=messages, task_type="analysis")

    async def generate_graph(
        self,
        requirements: str,
        selected_doc_types: list[str],
    ) -> dict:
        """Compose a workflow graph from templates based on selected doc types."""
        # Collect nodes from relevant templates
        all_nodes: dict[str, NodeTemplate] = {}
        template_slugs_needed: set[str] = set()

        for doc_key in selected_doc_types:
            mappings = DOC_TYPE_TO_TEMPLATE.get(doc_key, [])
            for template_key, slug_list in mappings:
                template = TEMPLATE_REGISTRY.get(template_key)
                if not template:
                    continue
                for nt in template.nodes:
                    if nt.slug in slug_list or nt.slug in template_slugs_needed:
                        all_nodes[nt.slug] = nt
                        template_slugs_needed.add(nt.slug)
                        # Also include dependencies
                        for dep in nt.depends_on:
                            template_slugs_needed.add(dep)

        # Second pass: ensure all dependencies are included
        for template_key, template in TEMPLATE_REGISTRY.items():
            for nt in template.nodes:
                if nt.slug in template_slugs_needed and nt.slug not in all_nodes:
                    all_nodes[nt.slug] = nt

        # Build graph JSON
        nodes_json = []
        edges_json = []

        for slug, nt in all_nodes.items():
            nodes_json.append({
                "slug": nt.slug,
                "label": nt.label,
                "branch": nt.branch,
                "node_type": nt.node_type.value,
                "requires_approval": nt.requires_approval,
                "config": nt.config,
            })
            for dep in nt.depends_on:
                if dep in all_nodes:
                    edges_json.append({"from_slug": dep, "to_slug": nt.slug})

        graph = {"nodes": nodes_json, "edges": edges_json}

        # Validate
        is_valid, errors = self.validate_graph(graph)
        if not is_valid:
            logger.error("Generated graph is invalid", errors=errors)
            raise ValueError(f"Invalid graph: {errors}")

        return graph

    def validate_graph(self, graph_json: dict) -> tuple[bool, list[str]]:
        """Validate graph structure: check for cycles, missing deps."""
        errors: list[str] = []
        slugs = {n["slug"] for n in graph_json.get("nodes", [])}

        # Check edge references
        for edge in graph_json.get("edges", []):
            if edge["from_slug"] not in slugs:
                errors.append(f"Edge references unknown node: {edge['from_slug']}")
            if edge["to_slug"] not in slugs:
                errors.append(f"Edge references unknown node: {edge['to_slug']}")

        # Cycle detection (Kahn's algorithm)
        in_degree: dict[str, int] = defaultdict(int)
        adj: dict[str, list[str]] = defaultdict(list)
        for s in slugs:
            in_degree.setdefault(s, 0)
        for edge in graph_json.get("edges", []):
            adj[edge["from_slug"]].append(edge["to_slug"])
            in_degree[edge["to_slug"]] += 1

        queue = [s for s, d in in_degree.items() if d == 0]
        visited = 0
        while queue:
            current = queue.pop(0)
            visited += 1
            for neighbor in adj[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if visited != len(slugs):
            errors.append("Cycle detected in graph")

        return len(errors) == 0, errors
