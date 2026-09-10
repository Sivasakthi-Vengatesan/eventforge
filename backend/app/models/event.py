import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, Enum, Index, UniqueConstraint
from backend.app.database.base import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class EventPriority(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"

class SystemMode(str, enum.Enum):
    NORMAL = "NORMAL"
    PRESSURE = "PRESSURE"
    DEGRADED = "DEGRADED"
    RECOVERY = "RECOVERY"

class EventStatus(str, enum.Enum):
    RECEIVED = "RECEIVED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    RETRYING = "RETRYING"
    FAILED = "FAILED"
    DLQ = "DLQ"
    DUPLICATE = "DUPLICATE"
    DELAYED = "DELAYED"
    BATCHED = "BATCHED"
    THROTTLED = "THROTTLED"

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_id = Column(String(128), nullable=False, index=True)
    provider = Column(String(64), nullable=False, index=True)
    event_type = Column(String(128), nullable=False, index=True)
    priority = Column(String(16), default=EventPriority.NORMAL.value, index=True, nullable=False)
    payload = Column(JSON, nullable=False)
    headers = Column(JSON, nullable=True)
    status = Column(String(32), default=EventStatus.RECEIVED.value, index=True, nullable=False)
    
    current_mode = Column(String(32), default=SystemMode.NORMAL.value, nullable=False)
    current_policy = Column(JSON, nullable=True)
    
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=5, nullable=False)
    
    received_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    queued_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    processing_duration_ms = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    last_error_type = Column(String(64), nullable=True)
    
    is_duplicate = Column(Boolean, default=False, nullable=False)
    duplicate_count = Column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint('provider', 'event_id', name='uq_provider_event_id'),
        Index('ix_events_status_received_at', 'status', 'received_at'),
        Index('ix_events_priority_status', 'priority', 'status'),
    )

class EventAttempt(Base):
    __tablename__ = "event_attempts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_id = Column(String(128), index=True, nullable=False)
    provider = Column(String(64), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    worker_id = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False)
    policy_mode = Column(String(32), default=SystemMode.NORMAL.value, nullable=False)
    started_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    response_status_code = Column(Integer, nullable=True)
    is_retryable = Column(Boolean, default=True, nullable=False)

class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    key = Column(String(256), unique=True, index=True, nullable=False)
    provider = Column(String(64), nullable=False)
    event_id = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_seen_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    hits = Column(Integer, default=1, nullable=False)
    status = Column(String(32), default="PROCESSED", nullable=False)

class PolicyDecisionRecord(Base):
    __tablename__ = "policy_decisions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    previous_mode = Column(String(32), nullable=False)
    new_mode = Column(String(32), nullable=False)
    reason = Column(Text, nullable=False)
    triggering_metric = Column(String(64), nullable=False)
    observed_value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    action = Column(Text, nullable=False)
    old_parameter = Column(String(128), nullable=True)
    new_parameter = Column(String(128), nullable=True)

class CircuitBreakerRecord(Base):
    __tablename__ = "circuit_breaker_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    service_name = Column(String(64), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    previous_state = Column(String(32), nullable=False)
    new_state = Column(String(32), nullable=False)
    failure_rate = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)

class DownstreamServiceRecord(Base):
    __tablename__ = "downstream_services"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    service_name = Column(String(64), unique=True, nullable=False)
    state = Column(String(32), default="CLOSED", nullable=False)
    failure_threshold = Column(Float, default=0.25, nullable=False)
    cooldown_seconds = Column(Integer, default=15, nullable=False)
    last_state_change = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    simulated_fault = Column(String(32), nullable=True)

