"""
Event Bus — lightweight in-memory event system for SSE agent log streaming.

Agents publish events (status updates, progress, errors) and the SSE endpoint
subscribes to stream them to the frontend in real-time.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from enum import StrEnum
from typing import AsyncIterator

from pydantic import BaseModel, Field


class EventType(StrEnum):
    """Types of events emitted by agents."""

    AGENT_START = "agent_start"
    AGENT_PROGRESS = "agent_progress"
    AGENT_COMPLETE = "agent_complete"
    AGENT_ERROR = "agent_error"
    PIPELINE_START = "pipeline_start"
    PIPELINE_COMPLETE = "pipeline_complete"
    PIPELINE_ERROR = "pipeline_error"


class AgentEvent(BaseModel):
    """A single event emitted during agent processing."""

    event_type: EventType
    agent_name: str = ""
    document_id: str = ""
    message: str = ""
    data: dict = Field(default_factory=dict)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class EventBus:
    """
    Simple async event bus for broadcasting agent events.

    Uses asyncio.Queue for each subscriber to implement a
    fan-out pub/sub pattern.
    """

    def __init__(self) -> None:
        self._subscribers: list[asyncio.Queue[AgentEvent]] = []

    def subscribe(self) -> asyncio.Queue[AgentEvent]:
        """
        Create a new subscription queue.

        Returns:
            An asyncio.Queue that will receive all future events.
        """
        queue: asyncio.Queue[AgentEvent] = asyncio.Queue()
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[AgentEvent]) -> None:
        """Remove a subscription queue."""
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    async def publish(self, event: AgentEvent) -> None:
        """Broadcast an event to all subscribers."""
        for queue in self._subscribers:
            await queue.put(event)

    async def stream(
        self, queue: asyncio.Queue[AgentEvent]
    ) -> AsyncIterator[AgentEvent]:
        """
        Async generator that yields events from a subscription queue.

        This is designed to be consumed by SSE endpoints.
        """
        try:
            while True:
                event = await queue.get()
                yield event
        except asyncio.CancelledError:
            return


# Global singleton event bus
event_bus = EventBus()
