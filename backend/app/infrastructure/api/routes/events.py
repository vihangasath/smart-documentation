"""
Events Route — GET /api/events (Server-Sent Events)

Real-time streaming of agent logs and pipeline status updates.
The frontend subscribes to this endpoint to show the "Agent Logs"
panel with live updates of what each agent is thinking/doing.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from app.application.event_bus import event_bus

router = APIRouter(prefix="/api", tags=["Events"])


@router.get(
    "/events",
    summary="Subscribe to agent events (SSE)",
    description="Server-Sent Events stream for real-time agent logs and pipeline status.",
)
async def event_stream(request: Request) -> EventSourceResponse:
    """
    SSE endpoint for real-time agent event streaming.

    The frontend connects to this endpoint and receives events as JSON:
    - agent_start: An agent begins processing
    - agent_progress: Progress update from an agent
    - agent_complete: Agent finished successfully
    - agent_error: Agent encountered an error
    - pipeline_start: Full pipeline begins
    - pipeline_complete: Full pipeline finished

    Each event contains: event_type, agent_name, document_id, message, data, timestamp.
    """

    async def event_generator():
        queue = event_bus.subscribe()
        try:
            async for event in event_bus.stream(queue):
                # Check if client disconnected
                if await request.is_disconnected():
                    break

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
        finally:
            event_bus.unsubscribe(queue)

    return EventSourceResponse(event_generator())
