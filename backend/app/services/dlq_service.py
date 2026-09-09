import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from backend.app.models.dlq import DeadLetterEvent
from backend.app.models.event import Event, EventStatus
from backend.app.queue.stream_manager import stream_manager
from backend.app.core.logging import logger

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class DLQService:
    @staticmethod
    async def send_to_dlq(
        db: AsyncSession,
        event: Event,
        failure_reason: str,
        error_trace: Optional[str] = None
    ) -> DeadLetterEvent:
        dlq_id = f"dlq_{uuid.uuid4().hex[:12]}"
        dlq_event = DeadLetterEvent(
            dlq_id=dlq_id,
            event_id=event.event_id,
            provider=event.provider,
            event_type=event.event_type,
            payload=event.payload,
            headers=event.headers,
            failure_reason=failure_reason,
            error_trace=error_trace or failure_reason,
            retry_count=event.retry_count,
            created_at=utc_now(),
            is_resolved=False
        )
        db.add(dlq_event)
        
        # Update original event status
        event.status = EventStatus.DLQ.value
        event.error_message = failure_reason
        event.completed_at = utc_now()
        
        await db.commit()
        await db.refresh(dlq_event)
        
        logger.warning(
            f"Event {event.event_id} moved to DLQ: {failure_reason}",
            extra={"event_id": event.event_id, "provider": event.provider, "dlq_id": dlq_id, "status": "DLQ"}
        )
        return dlq_event

    @staticmethod
    async def retry_dlq_event(db: AsyncSession, dlq_id: str) -> Optional[DeadLetterEvent]:
        stmt = select(DeadLetterEvent).where(DeadLetterEvent.dlq_id == dlq_id)
        res = await db.execute(stmt)
        dlq_event = res.scalar_one_or_none()
        if not dlq_event:
            return None

        # Re-queue to Redis stream
        await stream_manager.push_event(
            event_id=dlq_event.event_id,
            provider=dlq_event.provider,
            event_type=dlq_event.event_type,
            payload=dlq_event.payload,
            retry_count=0
        )
        
        # Update original event status if found
        evt_stmt = select(Event).where(Event.provider == dlq_event.provider, Event.event_id == dlq_event.event_id)
        evt_res = await db.execute(evt_stmt)
        orig_evt = evt_res.scalar_one_or_none()
        if orig_evt:
            orig_evt.status = EventStatus.QUEUED.value
            orig_evt.retry_count = 0
            orig_evt.error_message = None

        dlq_event.is_resolved = True
        dlq_event.resolved_at = utc_now()
        await db.commit()
        await db.refresh(dlq_event)
        
        logger.info(f"Retrying DLQ event {dlq_id} (re-queued to stream)")
        return dlq_event

    @staticmethod
    async def delete_dlq_event(db: AsyncSession, dlq_id: str) -> bool:
        stmt = delete(DeadLetterEvent).where(DeadLetterEvent.dlq_id == dlq_id)
        res = await db.execute(stmt)
        await db.commit()
        return res.rowcount > 0

dlq_service = DLQService()
