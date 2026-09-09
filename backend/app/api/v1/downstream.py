from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from backend.app.services.circuit_breaker import get_circuit_breaker
from backend.app.services.downstream_mock import get_downstream_service

router = APIRouter(prefix="/downstream", tags=["Downstream Services & Circuit Breaker"])

class DownstreamConfigUpdate(BaseModel):
    fault: Optional[str] = None  # None, "429", "500", "503", "timeout", "high_latency", "invalid_data"
    failure_rate: Optional[float] = None
    rate_limit_rate: Optional[float] = None
    latency_ms: Optional[int] = None
    reset_circuit_breaker: bool = False

@router.get(
    "",
    summary="Get downstream service health and circuit breaker state"
)
async def get_downstream_status():
    cb = get_circuit_breaker()
    return cb.get_status()

@router.get(
    "/status",
    summary="Get detailed downstream service status and active config"
)
async def get_downstream_detailed_status():
    cb = get_circuit_breaker()
    ds = get_downstream_service()
    return {
        "circuit_breaker": cb.get_status(),
        "service_config": {
            "failure_rate": ds.failure_rate,
            "rate_limit_rate": ds.rate_limit_rate,
            "latency_ms": ds.latency_ms
        }
    }

@router.post(
    "/config",
    summary="Configure downstream simulated faults and circuit breaker state"
)
async def configure_downstream(body: DownstreamConfigUpdate):
    cb = get_circuit_breaker()
    ds = get_downstream_service()
    
    if body.reset_circuit_breaker:
        cb.reset()
        
    if body.fault is not None:
        cb.set_simulated_fault(body.fault)
        
    if body.failure_rate is not None:
        ds.failure_rate = body.failure_rate
        
    if body.rate_limit_rate is not None:
        ds.rate_limit_rate = body.rate_limit_rate
        
    if body.latency_ms is not None:
        ds.latency_ms = body.latency_ms
        
    return {
        "status": "UPDATED",
        "circuit_breaker": cb.get_status(),
        "service_config": {
            "failure_rate": ds.failure_rate,
            "rate_limit_rate": ds.rate_limit_rate,
            "latency_ms": ds.latency_ms
        }
    }

@router.post(
    "/circuit-breaker/reset",
    summary="Force reset circuit breaker to CLOSED state"
)
async def reset_circuit_breaker_endpoint():
    cb = get_circuit_breaker()
    cb.reset()
    return {
        "status": "RESET",
        "circuit_breaker": cb.get_status()
    }
