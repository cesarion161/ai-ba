from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_type import DocumentType

DEFAULT_DOCUMENT_TYPES = [
    {
        "key": "lean_canvas",
        "label": "Lean Canvas",
        "description": "A one-page business model overview covering problem, solution, unique value proposition, customer segments, revenue streams, cost structure, key metrics, and unfair advantage.",
        "category": "strategy",
        "default_dependencies": [],
    },
    {
        "key": "competitor_analysis",
        "label": "Competitor Analysis",
        "description": "In-depth analysis of direct and indirect competitors including market positioning, strengths, weaknesses, pricing strategies, and differentiation opportunities.",
        "category": "research",
        "default_dependencies": [],
    },
    {
        "key": "market_sizing",
        "label": "Market Sizing (TAM/SAM/SOM)",
        "description": "Quantitative analysis of total addressable market, serviceable addressable market, and serviceable obtainable market with revenue projections.",
        "category": "research",
        "default_dependencies": ["competitor_analysis"],
    },
    {
        "key": "product_roadmap",
        "label": "Product Roadmap",
        "description": "Phased product development plan with feature prioritization, milestones, MVP definition, and timeline for future releases.",
        "category": "product",
        "default_dependencies": ["lean_canvas"],
    },
    {
        "key": "user_stories",
        "label": "User Stories & Personas",
        "description": "Detailed user personas with demographics, goals, and pain points, plus prioritized user stories with acceptance criteria.",
        "category": "product",
        "default_dependencies": ["lean_canvas"],
    },
    {
        "key": "architecture_doc",
        "label": "Technical Architecture",
        "description": "System architecture including tech stack recommendations, infrastructure design, data models, API design, and scalability considerations.",
        "category": "technical",
        "default_dependencies": ["product_roadmap", "user_stories"],
    },
    {
        "key": "execution_plan",
        "label": "Execution Plan",
        "description": "Go-to-market strategy with timeline, resource allocation, budget estimates, risk analysis, and key milestones for launch.",
        "category": "planning",
        "default_dependencies": ["market_sizing", "product_roadmap"],
    },
]


async def list_document_types(
    session: AsyncSession, active_only: bool = True
) -> list[DocumentType]:
    query = select(DocumentType).order_by(DocumentType.category, DocumentType.label)
    if active_only:
        query = query.where(DocumentType.is_active.is_(True))
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_by_key(session: AsyncSession, key: str) -> DocumentType | None:
    result = await session.execute(select(DocumentType).where(DocumentType.key == key))
    return result.scalar_one_or_none()


async def seed_defaults(session: AsyncSession) -> list[DocumentType]:
    created = []
    for dt_data in DEFAULT_DOCUMENT_TYPES:
        existing = await get_by_key(session, dt_data["key"])
        if existing:
            existing.label = dt_data["label"]
            existing.description = dt_data["description"]
            existing.category = dt_data["category"]
            existing.default_dependencies = dt_data["default_dependencies"]
            created.append(existing)
        else:
            dt = DocumentType(
                id=uuid.uuid4(),
                key=dt_data["key"],
                label=dt_data["label"],
                description=dt_data["description"],
                category=dt_data["category"],
                default_dependencies=dt_data["default_dependencies"],
            )
            session.add(dt)
            created.append(dt)
    await session.commit()
    return created
