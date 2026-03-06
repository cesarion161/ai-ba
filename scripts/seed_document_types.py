"""Seed default document types into the database."""

import asyncio

from app.models.database import async_session
from app.services.document_type_service import seed_defaults


async def main() -> None:
    async with async_session() as session:
        created = await seed_defaults(session)
        print(f"Seeded {len(created)} document types:")
        for dt in created:
            print(f"  - {dt.key}: {dt.label} ({dt.category})")


if __name__ == "__main__":
    asyncio.run(main())
