from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import redis.asyncio as aioredis
import structlog

from app.core.config import get_settings

logger = structlog.get_logger()

# Event type constants
NODE_STATUS_CHANGED = "node.status_changed"
NODE_RETRY = "node.retry"
NODE_FAILED = "node.failed"
NODE_COMPLETED = "node.completed"
WORKFLOW_COMPLETED = "workflow.completed"
CHAT_MESSAGE = "chat.message"
CHAT_TOKEN = "chat.token"
GRAPH_GENERATED = "graph.generated"
EXPORT_STARTED = "export.started"
EXPORT_PROGRESS = "export.progress"
EXPORT_COMPLETED = "export.completed"
EXPORT_FAILED = "export.failed"


class EventBus:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        # Always create a fresh connection for the current event loop.
        # Celery workers create a new event loop per task, making cached
        # connections from a previous (closed) loop unusable.
        import asyncio

        loop = asyncio.get_running_loop()
        if self._redis is None or getattr(self, "_loop_id", None) != id(loop):
            if self._redis is not None:
                try:
                    await self._redis.close()
                except Exception:
                    pass
            self._redis = aioredis.from_url(self.settings.REDIS_URL)
            self._loop_id = id(loop)
        return self._redis

    def _channel(self, project_id: str, node_slug: str | None = None) -> str:
        if node_slug:
            return f"workflow:{project_id}:node:{node_slug}"
        return f"workflow:{project_id}"

    async def publish(
        self,
        project_id: str,
        event_type: str,
        data: dict[str, Any],
        node_slug: str | None = None,
    ) -> None:
        redis = await self._get_redis()
        message = json.dumps({"event": event_type, "data": data})
        channel = self._channel(project_id, node_slug)
        await redis.publish(channel, message)
        logger.debug("event_published", channel=channel, event_type=event_type)

    async def subscribe(
        self, project_id: str, node_slug: str | None = None
    ) -> AsyncIterator[dict[str, Any]]:
        redis = await self._get_redis()
        pubsub = redis.pubsub()
        channel = self._channel(project_id, node_slug)
        await pubsub.subscribe(channel)

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    yield json.loads(message["data"])
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()

    async def close(self) -> None:
        if self._redis:
            await self._redis.close()
            self._redis = None


event_bus = EventBus()
