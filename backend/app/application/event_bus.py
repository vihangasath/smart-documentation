"""
Event Bus — lightweight in-memory pub/sub for SSE agent log streaming.

Events are scoped per document: a subscriber only receives events for the
document it asks for, and late subscribers are first sent a bounded replay of
what they missed. Subscriber queues are bounded; when a slow client falls
behind, its oldest events are dropped instead of growing memory without limit.

This is process-local. Move it to Redis pub/sub before running several workers.
"""

from __future__ import annotations

import asyncio
from collections import OrderedDict, deque
from collections.abc import AsyncIterator

from app.domain.entities.events import AgentEvent, EventType
from app.domain.ports.event_publisher_port import EventPublisherPort

TERMINAL_EVENTS = frozenset({EventType.PIPELINE_COMPLETE, EventType.PIPELINE_ERROR})


class EventBus(EventPublisherPort):
    """Per-document fan-out event bus with a replay buffer."""

    def __init__(
        self,
        replay_size: int = 200,
        queue_size: int = 500,
        max_documents: int = 500,
    ) -> None:
        self._replay_size = replay_size
        self._queue_size = max(queue_size, replay_size + 1)
        self._max_documents = max_documents
        self._history: OrderedDict[str, deque[AgentEvent]] = OrderedDict()
        self._subscribers: dict[str, set[asyncio.Queue[AgentEvent]]] = {}

    def subscribe(self, document_id: str) -> asyncio.Queue[AgentEvent]:
        """Create a queue pre-filled with the replay buffer for ``document_id``."""
        queue: asyncio.Queue[AgentEvent] = asyncio.Queue(maxsize=self._queue_size)
        for event in self._history.get(document_id, ()):
            queue.put_nowait(event)
        self._subscribers.setdefault(document_id, set()).add(queue)
        return queue

    def unsubscribe(self, document_id: str, queue: asyncio.Queue[AgentEvent]) -> None:
        """Remove a subscription queue."""
        queues = self._subscribers.get(document_id)
        if queues:
            queues.discard(queue)
            if not queues:
                del self._subscribers[document_id]

    async def publish(self, event: AgentEvent) -> None:
        """Record the event and deliver it to the document's subscribers."""
        doc_id = event.document_id
        if event.event_type == EventType.PIPELINE_START:
            # A new run starts with a clean slate so replays never mix runs.
            self._history.pop(doc_id, None)

        history = self._history.get(doc_id)
        if history is None:
            history = self._history[doc_id] = deque(maxlen=self._replay_size)
        else:
            self._history.move_to_end(doc_id)
        history.append(event)
        while len(self._history) > self._max_documents:
            self._history.popitem(last=False)

        for queue in list(self._subscribers.get(doc_id, ())):
            if queue.full():
                queue.get_nowait()  # drop the oldest event
            queue.put_nowait(event)

    async def stream(
        self, queue: asyncio.Queue[AgentEvent]
    ) -> AsyncIterator[AgentEvent]:
        """Yield events from a subscription queue until cancelled."""
        while True:
            yield await queue.get()
