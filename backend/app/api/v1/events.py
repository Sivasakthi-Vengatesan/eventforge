from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from backend.app.database.connection import get_db
from backend.app.models.event import Event, EventAttempt
from backend.app.schemas.event import EventSchema, EventDetailSchema, EventListResponse, EventAttemptSchema

router = APIRouter(prefix="/events", tags=["Event Explorer"])

@router.get("", response_model=EventListResponse, summary="Query and filter events")
async def list_events(
    provider: Optional[str] = None,
    status: Optional[str] = None,
    event_type: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    query = select(Event)
    count_query = select(func.count(Event.id))

    if provider:
        query = query.where(Event.provider == provider.lower())
        count_query = count_query.where(Event.provider == provider.lower())
    if status:
        query = query.where(Event.status == status.upper())
        count_query = count_query.where(Event.status == status.upper())
    if event_type:
        query = query.where(Event.event_type.ilike(f"%{event_type}%"))
        count_query = count_query.where(Event.event_type.ilike(f"%{event_type}%"))
    if search:
        query = query.where(Event.event_id.ilike(f"%{search}%"))
        count_query = count_query.where(Event.event_id.ilike(f"%{search}%"))

    total = (await db.execute(count_query)).scalar() or 0
    
    offset = (page - 1) * page_size
    query = query.order_by(desc(Event.id)).offset(offset).limit(page_size)
    
    result = await db.execute(query)
    events = result.scalars().all()

    return EventListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[EventSchema.model_validate(e) for e in events]
    )

@router.get("/{event_id}", response_model=EventDetailSchema, summary="Get full event lifecycle and attempt history")
async def get_event_detail(
    event_id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Event).where(Event.event_id == event_id)
    res = await db.execute(stmt)
    event = res.scalar_one_or_none()
    
    if not event:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")

    # Fetch attempts
    att_stmt = select(EventAttempt).where(EventAttempt.event_id == event_id).order_by(EventAttempt.attempt_number.asc())
    att_res = await db.execute(att_stmt)
    attempts = att_res.scalars().all()

    evt_data = EventSchema.model_validate(event).model_dump()
    evt_data["attempts"] = [EventAttemptSchema.model_validate(a) for a in attempts]
    
    return EventDetailSchema(**evt_data)
