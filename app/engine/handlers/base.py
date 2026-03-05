from __future__ import annotations

from typing import Any, Protocol

from app.models.workflow_node import NodeType


class NodeHandler(Protocol):
    async def execute(
        self,
        node_config: dict | None,
        input_data: dict[str, Any],
        user_feedback: str | None = None,
    ) -> dict[str, Any]: ...


NODE_HANDLERS: dict[NodeType, NodeHandler] = {}


def register_handler(node_type: NodeType):
    def decorator(cls: type[NodeHandler]):
        NODE_HANDLERS[node_type] = cls()
        return cls
    return decorator


def get_handler(node_type: NodeType) -> NodeHandler:
    if node_type not in NODE_HANDLERS:
        raise KeyError(f"No handler registered for {node_type.value}")
    return NODE_HANDLERS[node_type]
