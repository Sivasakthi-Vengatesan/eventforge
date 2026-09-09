import uuid
import pytest
from backend.app.database.connection import init_db, AsyncSessionLocal
from backend.app.models.event import Event, EventStatus
from backend.app.models.dlq import DeadLetterEvent
from backend.app.services.dlq_service import dlq_service

@pytest.mark.asyncio
async def test_dlq_lifecycle():
    await init_db()
    evt_id = f"evt_dlq_test_{uuid.uuid4().hex[:8]}"
    async with AsyncSessionLocal() as session:
        # 1. Create a failed event
        event = Event(
            event_id=evt_id,
            provider="razorpay",
            event_type="payment.failed",
            payload={"payment_id": "pay_98765"},
            status=EventStatus.FAILED.value,
            retry_count=5
        )
        session.add(event)
        await session.commit()
        await session.refresh(event)

        # 2. Send to DLQ
        dlq_item = await dlq_service.send_to_dlq(
            session,
            event=event,
            failure_reason="Exceeded MAX_RETRIES (5): 500 Internal Server Error"
        )
        assert dlq_item.id is not None
        assert dlq_item.dlq_id.startswith("dlq_")
        assert event.status == EventStatus.DLQ.value

        # 3. Retry DLQ event
        replayed = await dlq_service.retry_dlq_event(session, dlq_item.dlq_id)
        assert replayed.is_resolved is True
        assert event.status == EventStatus.QUEUED.value

        # 4. Delete DLQ event
        deleted = await dlq_service.delete_dlq_event(session, dlq_item.dlq_id)
        assert deleted is True
