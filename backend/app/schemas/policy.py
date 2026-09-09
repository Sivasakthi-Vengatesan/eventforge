from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict

class PolicyDecisionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    previous_mode: str
    new_mode: str
    reason: str
    triggering_metric: str
    observed_value: float
    threshold: float
    action: str
    old_parameter: Optional[str] = None
    new_parameter: Optional[str] = None

class SystemStateSchema(BaseModel):
    current_mode: str
    active_workers: int
    min_workers: int
    max_workers: int
    queue_depth: int
    queue_growth_rate: float
    ingestion_rate: float
    processing_rate: float
    worker_utilization: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    error_rate: float
    retry_rate: float
    http_429_rate: float
    circuit_breaker_state: str
    backpressure_active: bool
    delayed_events_count: int
    throttled_events_count: int
    batched_events_count: int
    priority_distribution: Dict[str, int]
    timestamp: datetime

class PolicyModeOverrideRequest(BaseModel):
    mode: str
    reason: Optional[str] = "Manual operator override"

class CircuitBreakerStatusSchema(BaseModel):
    service_name: str
    state: str
    failure_threshold: float
    cooldown_seconds: int
    failure_count: int
    last_state_change: datetime
    simulated_fault: Optional[str] = None
