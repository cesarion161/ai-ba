from __future__ import annotations

import json
from typing import Any, AsyncIterator

import redis.asyncio as aioredis
import structlog

from app.core.config import get_settings

logger = structlog.get_logger()


class EventBus:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(self.settings.REDIS_URL)
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
