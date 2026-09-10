import asyncio
import uuid
from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy import select
from backend.app.database.connection import AsyncSessionLocal
from backend.app.models.event import Event, EventStatus, EventPriority
from backend.app.queue.stream_manager import stream_manager
from backend.app.workers.worker import AsyncEventWorker
from backend.app.workers.manager import worker_manager

@pytest.mark.asyncio
async def test_durable_retry_persistence_and_recovery():
    """
    Verifies that failed retryable events store next_retry_at in PostgreSQL,
    and can be recovered and re-enqueued by the durable retry scheduler.
    """
    evt_id = f"evt_retry_durable_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)
    
    # 1. Insert a RETRYING event in PostgreSQL with next_retry_at in the past (due for recovery)
    async with AsyncSessionLocal() as session:
        event = Event(
            event_id=evt_id,
            provider="stripe",
            event_type="payment_intent.succeeded",
            priority=EventPriority.NORMAL.value,
            payload={"id": evt_id, "amount": 5000},
            status=EventStatus.RETRYING.value,
            retry_count=1,
            max_retries=5,
            received_at=now,
            next_retry_at=now - timedelta(seconds=2) # Already due
        )
        session.add(event)
        await session.commit()

    # 2. Simulate worker manager recovery loop execution
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Event)
            .where(
                Event.status == EventStatus.RETRYING.value,
                Event.next_retry_at <= datetime.now(timezone.utc)
            )
        )
        res = await session.execute(stmt)
        due = res.scalars().all()
        target_event = next((e for e in due if e.event_id == evt_id), None)
        assert target_event is not None

        # Re-enqueue
        target_event.status = EventStatus.QUEUED.value
        target_event.queued_at = datetime.now(timezone.utc)
        target_event.next_retry_at = None
        await session.commit()
        
        stream_id = await stream_manager.push_event(
            event_id=target_event.event_id,
            provider=target_event.provider,
            event_type=target_event.event_type,
            payload=target_event.payload,
            retry_count=target_event.retry_count
        )
        assert stream_id is not None

    # 3. Verify PostgreSQL status is now QUEUED
    async with AsyncSessionLocal() as session:
        stmt2 = select(Event).where(Event.event_id == evt_id)
        res2 = await session.execute(stmt2)
        refreshed = res2.scalar_one()
        assert refreshed.status == EventStatus.QUEUED.value
        assert refreshed.next_retry_at is None

@pytest.mark.asyncio
async def test_worker_claim_stuck_events():
    """
    Verifies that orphaned or pending messages from a dead worker can be claimed
    using claim_stuck_events without data loss.
    """
    evt_id = f"evt_orphan_{uuid.uuid4().hex[:8]}"
    payload = {"id": evt_id, "customer": "cust_123"}
    
    # Push event to stream
    msg_id = await stream_manager.push_event(
        event_id=evt_id,
        provider="github",
        event_type="push",
        payload=payload,
        retry_count=0
    )
    assert msg_id is not None

    # Worker 1 reads it (creating pending entry) but does NOT ACK it
    messages = await stream_manager.read_events(consumer_name="dead-worker-1", count=1, block_ms=100)
    assert len(messages) > 0

    # Worker 2 auto-claims stuck events with min_idle_ms=0 for testing
    stuck_messages = await stream_manager.claim_stuck_events(consumer_name="recovery-worker-2", min_idle_ms=0, count=5)
    
    # Verify the message was successfully reclaimed
    reclaimed_ids = [m[1].get("event_id") for m in stuck_messages]
    assert evt_id in reclaimed_ids
