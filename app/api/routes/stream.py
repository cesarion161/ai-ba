from __future__ import annotations

import json
import uuid

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from app.services.event_bus import event_bus

router = APIRouter(prefix="/api/projects/{project_id}/stream", tags=["streaming"])


@router.get("")
async def stream_project_events(project_id: uuid.UUID) -> EventSourceResponse:
    async def event_generator():  # type: ignore[no-untyped-def]
        async for event in event_bus.subscribe(str(project_id)):
            # Send as unnamed events so EventSource.onmessage receives them.
            # The event type is included in the JSON data payload.
            yield {"data": json.dumps(event)}

    return EventSourceResponse(event_generator())


@router.get("/nodes/{slug}")
async def stream_node_events(project_id: uuid.UUID, slug: str) -> EventSourceResponse:
    async def event_generator():  # type: ignore[no-untyped-def]
        async for event in event_bus.subscribe(str(project_id), node_slug=slug):
            yield {"data": json.dumps(event)}

    return EventSourceResponse(event_generator())
