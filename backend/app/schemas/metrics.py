from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict

class WorkerSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    current_event_id: Optional[str] = None
    current_event_provider: Optional[str] = None
    current_event_type: Optional[str] = None
    processed_count: int
    success_count: int
    failure_count: int
    total_processing_time_ms: float
    average_duration_ms: float
    last_heartbeat: datetime
    started_at: datetime

class DLQEventSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dlq_id: str
    event_id: str
    provider: str
    event_type: str
    payload: Dict[str, Any]
    headers: Optional[Dict[str, Any]] = None
    failure_reason: str
    error_trace: Optional[str] = None
    retry_count: int
    created_at: datetime
    resolved_at: Optional[datetime] = None
    is_resolved: bool

class DLQListResponse(BaseModel):
    total: int
    items: List[DLQEventSchema]

class SystemMetricsSummary(BaseModel):
    total_events: int
    events_per_second: float
    success_count: int
    failed_count: int
    retrying_count: int
    dlq_count: int
    duplicate_count: int
    success_rate: float
    queue_depth: int
    pending_events: int
    active_workers: int
    total_workers: int
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    error_rate: Optional[float] = 0.0
    retry_rate: Optional[float] = 0.0
    http_429_rate: Optional[float] = 0.0
    current_mode: Optional[str] = "NORMAL"
    circuit_breaker_state: Optional[str] = "CLOSED"
    delayed_count: Optional[int] = 0
    throttled_count: Optional[int] = 0
    batched_count: Optional[int] = 0
    priority_distribution: Optional[Dict[str, int]] = None
    timestamp: Optional[str] = None


class HealthCheckResponse(BaseModel):
    status: str
    database: str
    redis: str
    workers: str
    timestamp: datetime
