from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_type import DocumentType

DEFAULT_DOCUMENT_TYPES: list[dict[str, Any]] = [
    {
        "key": "lean_canvas",
        "label": "Lean Canvas",
        "description": (
            "A one-page business model overview covering problem, "
            "solution, unique value proposition, customer segments, "
            "revenue streams, cost structure, key metrics, "
            "and unfair advantage."
        ),
        "category": "strategy",
        "default_dependencies": [],
    },
    {
        "key": "competitor_analysis",
        "label": "Competitor Analysis",
        "description": (
            "In-depth analysis of direct and indirect competitors "
            "including market positioning, strengths, weaknesses, "
            "pricing strategies, and differentiation opportunities."
        ),
        "category": "research",
        "default_dependencies": [],
    },
    {
        "key": "market_sizing",
        "label": "Market Sizing (TAM/SAM/SOM)",
        "description": (
            "Quantitative analysis of total addressable market, "
            "serviceable addressable market, and serviceable "
            "obtainable market with revenue projections."
        ),
        "category": "research",
        "default_dependencies": ["competitor_analysis"],
    },
    {
        "key": "product_roadmap",
        "label": "Product Roadmap",
        "description": (
            "Phased product development plan with feature "
            "prioritization, milestones, MVP definition, "
            "and timeline for future releases."
        ),
        "category": "product",
        "default_dependencies": ["lean_canvas"],
    },
    {
        "key": "user_stories",
        "label": "User Stories & Personas",
        "description": (
            "Detailed user personas with demographics, goals, "
            "and pain points, plus prioritized user stories "
            "with acceptance criteria."
        ),
        "category": "product",
        "default_dependencies": ["lean_canvas"],
    },
    {
        "key": "architecture_doc",
        "label": "Technical Architecture",
        "description": (
            "System architecture including tech stack "
            "recommendations, infrastructure design, data models, "
            "API design, and scalability considerations."
        ),
        "category": "technical",
        "default_dependencies": ["product_roadmap", "user_stories"],
    },
    {
        "key": "execution_plan",
        "label": "Execution Plan",
        "description": (
            "Go-to-market strategy with timeline, resource "
            "allocation, budget estimates, risk analysis, "
            "and key milestones for launch."
        ),
        "category": "planning",
        "default_dependencies": ["market_sizing", "product_roadmap"],
    },
    {
        "key": "feasibility_assessment",
        "label": "Feasibility Assessment",
        "description": (
            "Seven-axis viability stress test covering business, "
            "technical, legal, operational, financial, schedule, "
            "and strategic feasibility with go/no-go recommendation."
        ),
        "category": "strategy",
        "default_dependencies": ["lean_canvas"],
    },
    {
        "key": "brd",
        "label": "Business Requirements Document",
        "description": (
            "Formal BRD with numbered requirements, measurable "
            "acceptance criteria, business rules catalog, and "
            "traceability to business objectives."
        ),
        "category": "requirements",
        "default_dependencies": ["lean_canvas"],
    },
    {
        "key": "business_rules",
        "label": "Business Rules Catalog",
        "description": (
            "Comprehensive catalog of business rules across "
            "access control, validation, pricing, notifications, "
            "compliance, and operational categories."
        ),
        "category": "requirements",
        "default_dependencies": [],
    },
    {
        "key": "process_model",
        "label": "Business Process Model",
        "description": (
            "Current and future-state process flows with "
            "Mermaid diagrams, service blueprint, RACI matrix, "
            "and process improvement opportunities."
        ),
        "category": "requirements",
        "default_dependencies": [],
    },
    {
        "key": "api_contracts",
        "label": "API & Event Contracts",
        "description": (
            "API endpoint specifications with request/response "
            "schemas, error codes, rate limits, versioning "
            "strategy, and event contracts."
        ),
        "category": "technical",
        "default_dependencies": ["architecture_doc"],
    },
    {
        "key": "data_model_spec",
        "label": "Data Model Specification",
        "description": (
            "Entity definitions with field-level detail, PII "
            "classification, retention policies, ER diagrams, "
            "and migration strategy."
        ),
        "category": "technical",
        "default_dependencies": ["architecture_doc"],
    },
    {
        "key": "qa_strategy",
        "label": "QA & Test Strategy",
        "description": (
            "Test pyramid, performance and security testing "
            "plans, UAT procedures, quality gates, and "
            "environment strategy."
        ),
        "category": "delivery",
        "default_dependencies": ["user_stories", "architecture_doc"],
    },
    {
        "key": "traceability_matrix",
        "label": "Traceability Matrix",
        "description": (
            "Cross-reference matrix linking business objectives "
            "to requirements, features, user stories, test "
            "cases, and acceptance criteria."
        ),
        "category": "delivery",
        "default_dependencies": ["brd", "user_stories", "qa_strategy"],
    },
]


CATEGORY_ORDER = [
    "strategy",
    "research",
    "requirements",
    "product",
    "technical",
    "planning",
    "delivery",
]
_cat_index = {cat: i for i, cat in enumerate(CATEGORY_ORDER)}


async def list_document_types(
    session: AsyncSession, active_only: bool = True
) -> list[DocumentType]:
    query = select(DocumentType).order_by(DocumentType.category, DocumentType.label)
    if active_only:
        query = query.where(DocumentType.is_active.is_(True))
    result = await session.execute(query)
    docs = list(result.scalars().all())
    docs.sort(key=lambda d: (_cat_index.get(d.category, 99), d.label))
    return docs


async def get_by_key(session: AsyncSession, key: str) -> DocumentType | None:
    result = await session.execute(select(DocumentType).where(DocumentType.key == key))
    return result.scalar_one_or_none()


async def seed_defaults(session: AsyncSession) -> list[DocumentType]:
    created: list[DocumentType] = []
    for dt_data in DEFAULT_DOCUMENT_TYPES:
        existing = await get_by_key(session, str(dt_data["key"]))
        if existing:
            existing.label = str(dt_data["label"])
            existing.description = str(dt_data["description"])
            existing.category = str(dt_data["category"])
            existing.default_dependencies = dt_data["default_dependencies"]
            created.append(existing)
        else:
            dt = DocumentType(
                id=uuid.uuid4(),
                key=str(dt_data["key"]),
                label=str(dt_data["label"]),
                description=str(dt_data["description"]),
                category=str(dt_data["category"]),
                default_dependencies=dt_data["default_dependencies"],
            )
            session.add(dt)
            created.append(dt)
    await session.commit()
    return created
