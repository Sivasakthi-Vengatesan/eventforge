from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

@dataclass
class SystemState:
    current_mode: str = "NORMAL"
    active_workers: int = 4
    min_workers: int = 2
    max_workers: int = 8
    
    queue_depth: int = 0
    queue_growth_rate: float = 0.0
    ingestion_rate: float = 0.0
    processing_rate: float = 0.0
    worker_utilization: float = 0.0
    
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    
    error_rate: float = 0.0
    retry_rate: float = 0.0
    http_429_rate: float = 0.0
    
    circuit_breaker_state: str = "CLOSED"
    backpressure_active: bool = False
    
    delayed_events_count: int = 0
    throttled_events_count: int = 0
    batched_events_count: int = 0
    
    priority_distribution: Dict[str, int] = field(default_factory=lambda: {
        "CRITICAL": 0,
        "HIGH": 0,
        "NORMAL": 0,
        "LOW": 0
    })
    
    timestamp: datetime = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_mode": self.current_mode,
            "active_workers": self.active_workers,
            "min_workers": self.min_workers,
            "max_workers": self.max_workers,
            "queue_depth": self.queue_depth,
            "queue_growth_rate": round(self.queue_growth_rate, 2),
            "ingestion_rate": round(self.ingestion_rate, 2),
            "processing_rate": round(self.processing_rate, 2),
            "worker_utilization": round(self.worker_utilization, 2),
            "p50_latency_ms": round(self.p50_latency_ms, 2),
            "p95_latency_ms": round(self.p95_latency_ms, 2),
            "p99_latency_ms": round(self.p99_latency_ms, 2),
            "error_rate": round(self.error_rate, 3),
            "retry_rate": round(self.retry_rate, 3),
            "http_429_rate": round(self.http_429_rate, 3),
            "circuit_breaker_state": self.circuit_breaker_state,
            "backpressure_active": self.backpressure_active,
            "delayed_events_count": self.delayed_events_count,
            "throttled_events_count": self.throttled_events_count,
            "batched_events_count": self.batched_events_count,
            "priority_distribution": self.priority_distribution,
            "timestamp": self.timestamp.isoformat()
        }

class SystemStateManager:
    def __init__(self):
        self._state = SystemState()
        self._last_queue_depth = 0
        self._last_queue_timestamp = utc_now()

    def get_state(self) -> SystemState:
        return self._state

    def update_metrics(
        self,
        queue_depth: int,
        ingestion_rate: float,
        processing_rate: float,
        worker_utilization: float,
        p50: float,
        p95: float,
        p99: float,
        error_rate: float,
        retry_rate: float,
        http_429_rate: float,
        active_workers: int,
        priority_counts: Optional[Dict[str, int]] = None,
        circuit_state: str = "CLOSED"
    ) -> SystemState:
        now = utc_now()
        dt = (now - self._last_queue_timestamp).total_seconds()
        
        if dt > 0:
            growth_rate = (queue_depth - self._last_queue_depth) / dt
        else:
            growth_rate = 0.0

        self._last_queue_depth = queue_depth
        self._last_queue_timestamp = now

        self._state.queue_depth = queue_depth
        self._state.queue_growth_rate = growth_rate
        self._state.ingestion_rate = ingestion_rate
        self._state.processing_rate = processing_rate
        self._state.worker_utilization = worker_utilization
        self._state.p50_latency_ms = p50
        self._state.p95_latency_ms = p95
        self._state.p99_latency_ms = p99
        self._state.error_rate = error_rate
        self._state.retry_rate = retry_rate
        self._state.http_429_rate = http_429_rate
        self._state.active_workers = active_workers
        self._state.circuit_breaker_state = circuit_state
        self._state.timestamp = now

        if priority_counts:
            self._state.priority_distribution = priority_counts

        return self._state
