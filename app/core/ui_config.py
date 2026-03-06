"""Centralized UI color/theme configuration."""

from __future__ import annotations

from pydantic import BaseModel


class StatusColors(BaseModel):
    attention: str = "#F59E0B"
    working: str = "#3B82F6"
    error: str = "#EF4444"
    approved: str = "#22C55E"
    pending: str = "#6B7280"
    running: str = "#3B82F6"
    rejected: str = "#F97316"


class NodeStatusColorMap(BaseModel):
    pending: str = "#6B7280"
    ready: str = "#6B7280"
    running: str = "#3B82F6"
    awaiting_review: str = "#F59E0B"
    approved: str = "#22C55E"
    rejected: str = "#F97316"
    failed: str = "#EF4444"
    skipped: str = "#6B7280"


class ChatPhaseColorMap(BaseModel):
    gathering_requirements: str = "#3B82F6"
    selecting_documents: str = "#F59E0B"
    generating_graph: str = "#8B5CF6"
    graph_ready: str = "#22C55E"
    executing: str = "#3B82F6"
    completed: str = "#22C55E"


class UIConfig(BaseModel):
    status_colors: StatusColors = StatusColors()
    node_status_colors: NodeStatusColorMap = NodeStatusColorMap()
    chat_phase_colors: ChatPhaseColorMap = ChatPhaseColorMap()
