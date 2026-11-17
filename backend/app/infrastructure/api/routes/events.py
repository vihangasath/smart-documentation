"""
Events Route — GET /api/events/{document_id} (Server-Sent Events)

Streams the agent log for ONE document the caller owns. Late subscribers first
receive a replay of earlier events; the stream ends after the pipeline's
terminal event.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from app.application.event_bus import TERMINAL_EVENTS
from app.infrastructure.api.dependencies import (
    Container,
    OwnedDocument,
    get_container,
    get_owned_document,
)

router = APIRouter(prefix="/api", tags=["Events"])


@router.get(
    "/events/{document_id}",
    summary="Subscribe to a document's agent events (SSE)",
    description=(
        "Events: agent_start, agent_progress, agent_complete, agent_error, "
        "pipeline_start, pipeline_complete, pipeline_error. Each carries "
        "agent_name, document_id, message, data and an ISO timestamp."
    ),
)
async def event_stream(
    owned: OwnedDocument = Depends(get_owned_document),
    container: Container = Depends(get_container),
) -> EventSourceResponse:
    document_id = owned.document.id
    bus = container.events

    async def event_generator():
        queue = bus.subscribe(document_id)
        try:
            async for event in bus.stream(queue):
                yield {
                    "event": event.event_type.value,
                    "data": json.dumps(
                        {
                            "agent_name": event.agent_name,
                            "document_id": event.document_id,
                            "message": event.message,
                            "data": event.data,
                            "timestamp": event.timestamp.isoformat(),
                        }
                    ),
                }
                if event.event_type in TERMINAL_EVENTS:
                    break
        finally:
            bus.unsubscribe(document_id, queue)

    return EventSourceResponse(event_generator())
