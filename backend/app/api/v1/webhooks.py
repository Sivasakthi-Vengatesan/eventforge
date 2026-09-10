import json
import time
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Request, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database.connection import get_db
from backend.app.schemas.webhook import WebhookIngestResponse
from backend.app.security.hmac import verify_webhook_security, WebhookSecurityError
from backend.app.services.idempotency import idempotency_service
from backend.app.queue.stream_manager import stream_manager
from backend.app.models.event import EventStatus
from backend.app.adaptive.priority_router import PriorityRouter
from backend.app.adaptive.policy_engine import get_policy_engine
from backend.app.monitoring.websocket_manager import ws_manager
from backend.app.core.logging import logger

router = APIRouter(prefix="/webhooks", tags=["Webhook Ingestion Gateway"])

def extract_event_id_and_type(provider: str, payload: dict, headers: dict) -> tuple[str, str]:
    prov = provider.lower()
    
    if prov == "stripe":
        event_id = payload.get("id") or f"evt_str_{uuid.uuid4().hex[:14]}"
        event_type = payload.get("type", "payment_intent.succeeded")
    elif prov == "razorpay":
        event_id = payload.get("id") or payload.get("event_id") or f"rzp_evt_{uuid.uuid4().hex[:14]}"
        event_type = payload.get("event", "payment.captured")
    elif prov == "github":
        event_id = headers.get("x-github-delivery") or payload.get("id") or f"gh_del_{uuid.uuid4().hex[:14]}"
        event_type = headers.get("x-github-event") or payload.get("action") or "push"
    else:
        event_id = payload.get("event_id") or payload.get("id") or f"gen_{uuid.uuid4().hex[:14]}"
        event_type = payload.get("event_type") or payload.get("type") or "generic.event"
        
    return str(event_id), str(event_type)

@router.post(
    "/{provider}",
    response_model=WebhookIngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest incoming webhook with HMAC security & async streaming"
)
async def ingest_webhook(
    provider: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    start_time = time.perf_counter()
    raw_body = await request.body()
    headers = dict(request.headers)

    # 1. Security & Signature Verification
    try:
        verify_webhook_security(provider, raw_body, headers)
    except WebhookSecurityError as sec_err:
        logger.warning(
            f"Webhook signature rejected for {provider}: {sec_err.message}",
            extra={"provider": provider, "status": "REJECTED"}
        )
        raise HTTPException(status_code=sec_err.status_code, detail=sec_err.message)

    # 2. Parse JSON Payload
    try:
        payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except Exception as parse_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Malformed JSON payload: {str(parse_err)}"
        )

    # 3. Extract Identity & Priority Classification
    event_id, event_type = extract_event_id_and_type(provider, payload, headers)
    priority = PriorityRouter.classify(provider, event_type, payload)
    
    policy_engine = get_policy_engine()
    current_mode = policy_engine.current_mode

    # 4. Atomic Idempotency Check & Minimal Persistence
    is_duplicate, event_record = await idempotency_service.check_and_record_event(
        db=db,
        provider=provider,
        event_id=event_id,
        event_type=event_type,
        payload=payload,
        headers=headers,
        priority=priority,
        current_mode=current_mode
    )

    now_iso = datetime.now(timezone.utc).isoformat()

    if is_duplicate:
        # Broadcast duplicate event detection
        await ws_manager.broadcast("EVENT_DUPLICATE_RECEIVED", {
            "event_id": event_id,
            "provider": provider,
            "event_type": event_type,
            "priority": priority,
            "duplicate_count": event_record.duplicate_count,
            "status": "DUPLICATE"
        })
        return WebhookIngestResponse(
            status="DUPLICATE",
            event_id=event_id,
            provider=provider,
            event_type=event_type,
            received_at=now_iso,
            message=f"Duplicate webhook ignored (seen {event_record.duplicate_count} times). Idempotency preserved."
        )

    # 5. Push to Redis Stream with Priority Tag
    stream_msg_id = await stream_manager.push_event(
        event_id=event_id,
        provider=provider,
        event_type=event_type,
        payload=payload,
        retry_count=0
    )

    # Update event state to QUEUED
    event_record.status = EventStatus.QUEUED.value
    event_record.queued_at = datetime.now(timezone.utc)
    await db.commit()

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    # 6. Real-Time Observability Broadcast
    await ws_manager.broadcast("EVENT_RECEIVED", {
        "event_id": event_id,
        "provider": provider,
        "event_type": event_type,
        "priority": priority,
        "status": "QUEUED",
        "stream_msg_id": stream_msg_id,
        "received_at": now_iso
    })

    logger.info(f"Webhook {provider}:{event_id} [{priority}] accepted and queued to stream in {elapsed_ms}ms.")

    # 7. Fast HTTP 202 Accepted Response
    return WebhookIngestResponse(
        status="ACCEPTED",
        event_id=event_id,
        provider=provider,
        event_type=event_type,
        received_at=now_iso,
        message=f"Webhook [{priority}] accepted, validated, and queued for asynchronous processing in {elapsed_ms}ms."
    )


