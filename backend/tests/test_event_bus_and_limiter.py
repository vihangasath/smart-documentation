import asyncio

from app.application.event_bus import EventBus
from app.domain.entities.events import AgentEvent, EventType
from app.infrastructure.api.rate_limit import SlidingWindowLimiter


def ev(doc, kind=EventType.AGENT_PROGRESS, msg=""):
    return AgentEvent(event_type=kind, document_id=doc, message=msg)


async def test_events_are_scoped_per_document():
    bus = EventBus()
    q = bus.subscribe("a")
    await bus.publish(ev("a", msg="1"))
    await bus.publish(ev("b", msg="2"))
    assert q.qsize() == 1 and q.get_nowait().message == "1"


async def test_late_subscriber_gets_replay_and_new_run_resets():
    bus = EventBus()
    await bus.publish(ev("a", msg="old"))
    await bus.publish(ev("a", EventType.PIPELINE_COMPLETE, "old-done"))

    q = bus.subscribe("a")
    assert [q.get_nowait().message for _ in range(q.qsize())] == ["old", "old-done"]

    await bus.publish(ev("a", EventType.PIPELINE_START, "new"))
    late = bus.subscribe("a")
    assert [late.get_nowait().message for _ in range(late.qsize())] == ["new"]


async def test_slow_subscriber_drops_oldest_instead_of_growing():
    bus = EventBus(replay_size=2, queue_size=3)
    q = bus.subscribe("a")
    for i in range(10):
        await bus.publish(ev("a", msg=str(i)))
    assert q.qsize() == q.maxsize
    assert q.get_nowait().message == "7"


async def test_unsubscribe_cleans_up():
    bus = EventBus()
    q = bus.subscribe("a")
    bus.unsubscribe("a", q)
    assert "a" not in bus._subscribers
    await asyncio.sleep(0)


def test_rate_limiter_window():
    now = [0.0]
    limiter = SlidingWindowLimiter(2, 10, clock=lambda: now[0])
    assert limiter.hit("k") is None
    assert limiter.hit("k") is None
    assert limiter.hit("k") is not None  # blocked
    assert limiter.hit("other") is None  # per key
    now[0] = 11
    assert limiter.hit("k") is None
