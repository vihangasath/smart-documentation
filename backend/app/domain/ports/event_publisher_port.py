"""Event Publisher Port — how use cases announce progress to the outside world."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.events import AgentEvent


class EventPublisherPort(ABC):
    """Port for publishing agent events."""

    @abstractmethod
    async def publish(self, event: AgentEvent) -> None:
        """Publish an event to interested subscribers."""
        ...
