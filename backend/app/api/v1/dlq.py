from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from backend.app.database.connection import get_db
from backend.app.models.dlq import DeadLetterEvent
from backend.app.schemas.metrics import DLQEventSchema, DLQListResponse
from backend.app.services.dlq_service import dlq_service

router = APIRouter(prefix="/dlq", tags=["Dead Letter Queue"])

@router.get("", response_model=DLQListResponse, summary="List unrecoverable events in DLQ")
async def list_dlq(db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count(DeadLetterEvent.id)))).scalar() or 0
    res = await db.execute(select(DeadLetterEvent).order_by(desc(DeadLetterEvent.id)))
    events = res.scalars().all()
    return DLQListResponse(
        total=total,
        items=[DLQEventSchema.model_validate(e) for e in events]
    )

@router.get("/{dlq_id}", response_model=DLQEventSchema, summary="Inspect DLQ event detail")
async def get_dlq_event(dlq_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(DeadLetterEvent).where(DeadLetterEvent.dlq_id == dlq_id)
    res = await db.execute(stmt)
    event = res.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail=f"DLQ record {dlq_id} not found")
    return DLQEventSchema.model_validate(event)

@router.post("/{dlq_id}/retry", summary="Replay DLQ event back into processing stream")
async def retry_dlq_event(dlq_id: str, db: AsyncSession = Depends(get_db)):
    ret = await dlq_service.retry_dlq_event(db, dlq_id)
    if not ret:
        raise HTTPException(status_code=404, detail=f"DLQ record {dlq_id} not found")
    return {"status": "REPLAYED", "message": f"Event {ret.event_id} successfully re-enqueued to stream"}

@router.delete("/{dlq_id}", summary="Purge event from DLQ")
async def delete_dlq_event(dlq_id: str, db: AsyncSession = Depends(get_db)):
    deleted = await dlq_service.delete_dlq_event(db, dlq_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"DLQ record {dlq_id} not found")
    return {"status": "DELETED", "message": f"DLQ record {dlq_id} deleted"}
