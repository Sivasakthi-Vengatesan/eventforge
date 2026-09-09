from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.app.database.connection import get_db
from backend.app.adaptive.policy_engine import get_policy_engine
from backend.app.schemas.policy import SystemStateSchema, PolicyDecisionSchema, PolicyModeOverrideRequest
from backend.app.models.event import PolicyDecisionRecord

router = APIRouter(prefix="/policies", tags=["Adaptive Policy Engine"])

@router.get(
    "/current",
    summary="Get current adaptive system state and policy parameters"
)
async def get_current_policy():
    engine = get_policy_engine()
    state = engine.system_state
    return {
        "current_mode": state.current_mode,
        "active_workers": state.active_workers,
        "min_workers": state.min_workers,
        "max_workers": state.max_workers,
        "queue_depth": state.queue_depth,
        "queue_growth_rate": state.queue_growth_rate,
        "ingestion_rate": state.ingestion_rate,
        "processing_rate": state.processing_rate,
        "worker_utilization": state.worker_utilization,
        "p50_latency_ms": state.p50_latency_ms,
        "p95_latency_ms": state.p95_latency_ms,
        "p99_latency_ms": state.p99_latency_ms,
        "error_rate": state.error_rate,
        "retry_rate": state.retry_rate,
        "http_429_rate": state.http_429_rate,
        "circuit_breaker_state": state.circuit_breaker_state,
        "backpressure_active": state.backpressure_active,
        "delayed_events_count": state.delayed_events_count,
        "throttled_events_count": state.throttled_events_count,
        "batched_events_count": state.batched_events_count,
        "priority_distribution": state.priority_distribution,
        "timestamp": state.timestamp.isoformat()
    }

@router.get(
    "/state",
    summary="Alias for current system state"
)
async def get_policy_state_alias():
    return await get_current_policy()

@router.get(
    "/history",
    summary="Get chronological explainable policy decisions"
)
async def get_policy_history(
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(PolicyDecisionRecord).order_by(desc(PolicyDecisionRecord.timestamp)).limit(limit)
    res = await db.execute(stmt)
    records = res.scalars().all()
    
    return [
        {
            "id": r.id,
            "decision_id": f"dec_{r.id}",
            "timestamp": r.timestamp.isoformat(),
            "previous_mode": r.previous_mode,
            "target_mode": r.new_mode,
            "new_mode": r.new_mode,
            "trigger_reason": r.reason,
            "reason": r.reason,
            "triggering_metric": r.triggering_metric,
            "observed_value": r.observed_value,
            "threshold": r.threshold,
            "action": r.action,
            "queue_depth": 0,
            "p95_latency_ms": 0.0,
            "error_rate": 0.0,
            "rate_limit_ratio": 0.0,
            "concurrency_target": int(r.new_parameter) if r.new_parameter and r.new_parameter.isdigit() else 4,
            "retry_multiplier": 1.0,
            "backpressure_applied": False,
            "batching_enabled": False,
            "old_parameter": r.old_parameter,
            "new_parameter": r.new_parameter
        }
        for r in records
    ]

@router.get(
    "/decisions",
    summary="Alias for policy decisions ledger"
)
async def get_policy_decisions_alias(
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    return await get_policy_history(limit=limit, db=db)

@router.post(
    "/mode",
    summary="Manually trigger mode override for demonstration or chaos drills"
)
async def override_policy_mode(body: PolicyModeOverrideRequest):
    allowed_modes = ["NORMAL", "PRESSURE", "DEGRADED", "RECOVERY"]
    target_mode = body.mode.upper()
    if target_mode not in allowed_modes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid mode: {body.mode}. Allowed: {allowed_modes}"
        )
    
    engine = get_policy_engine()
    result = await engine.manual_override(target_mode, reason=body.reason or "Manual operator override")
    return {"status": "SUCCESS", "transition": result}

@router.post(
    "/override",
    summary="Alias for manual mode override"
)
async def override_policy_mode_alias(body: PolicyModeOverrideRequest):
    return await override_policy_mode(body)

@router.post(
    "/auto",
    summary="Clear manual override and resume autonomous dynamic evaluation"
)
async def resume_auto_policy():
    engine = get_policy_engine()
    engine._manual_mode_override = None
    return {"status": "SUCCESS", "message": "Resumed autonomous feedback evaluation"}
