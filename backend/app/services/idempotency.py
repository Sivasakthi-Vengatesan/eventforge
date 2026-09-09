import asyncio
from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from backend.app.models.event import Event, IdempotencyRecord, EventStatus
from backend.app.core.logging import logger

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class IdempotencyService:
    def __init__(self):
        self._memory_lock = asyncio.Lock()

    async def check_and_record_event(
        self,
        db: AsyncSession,
        provider: str,
        event_id: str,
        event_type: str,
        payload: dict,
        headers: Optional[dict] = None,
        priority: str = "NORMAL",
        current_mode: str = "NORMAL"
    ) -> Tuple[bool, Event]:
        """
        Atomically inspects if (provider, event_id) exists.
        If duplicate: updates duplicate counter and returns (True, existing_event).
        If new: creates and flushes Event & IdempotencyRecord, returning (False, new_event).
        Protects against race conditions on concurrent identical bursts.
        """
        idempotency_key = f"{provider}:{event_id}"
        
        # 1. Check existing event
        stmt = select(Event).where(Event.provider == provider, Event.event_id == event_id)
        result = await db.execute(stmt)
        existing_event = result.scalar_one_or_none()

        if existing_event:
            existing_event.is_duplicate = True
            existing_event.duplicate_count += 1
            
            rec_stmt = select(IdempotencyRecord).where(IdempotencyRecord.key == idempotency_key)
            rec_res = await db.execute(rec_stmt)
            rec = rec_res.scalar_one_or_none()
            if rec:
                rec.hits += 1
                rec.last_seen_at = utc_now()
                
            await db.commit()
            await db.refresh(existing_event)
            logger.info(
                f"Duplicate event detected for {provider}:{event_id} (seen {existing_event.duplicate_count} times)",
                extra={"event_id": event_id, "provider": provider, "status": "DUPLICATE"}
            )
            return True, existing_event

        # 2. Try to insert new event
        try:
            new_event = Event(
                event_id=event_id,
                provider=provider,
                event_type=event_type,
                priority=priority,
                payload=payload,
                headers=headers or {},
                status=EventStatus.RECEIVED.value,
                current_mode=current_mode,
                received_at=utc_now(),
                is_duplicate=False,
                duplicate_count=0
            )
            db.add(new_event)
            
            new_record = IdempotencyRecord(
                key=idempotency_key,
                provider=provider,
                event_id=event_id,
                created_at=utc_now(),
                last_seen_at=utc_now(),
                hits=1,
                status="RECEIVED"
            )
            db.add(new_record)
            
            await db.commit()
            await db.refresh(new_event)
            return False, new_event
        except IntegrityError:
            await db.rollback()
            # Concurrent duplicate won the race; re-fetch and treat as duplicate
            stmt2 = select(Event).where(Event.provider == provider, Event.event_id == event_id)
            res2 = await db.execute(stmt2)
            concurrent_event = res2.scalar_one_or_none()
            if concurrent_event:
                concurrent_event.is_duplicate = True
                concurrent_event.duplicate_count += 1
                await db.commit()
                await db.refresh(concurrent_event)
                return True, concurrent_event
            raise

idempotency_service = IdempotencyService()
