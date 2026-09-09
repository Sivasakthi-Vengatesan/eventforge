import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Float
from backend.app.database.base import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class WorkerStatus(str, enum.Enum):
    STARTING = "STARTING"
    HEALTHY = "HEALTHY"
    BUSY = "BUSY"
    DRAINING = "DRAINING"
    FAILED = "FAILED"
    STOPPED = "STOPPED"

class Worker(Base):
    __tablename__ = "workers"

    id = Column(String(64), primary_key=True)
    status = Column(String(32), default=WorkerStatus.STARTING.value, nullable=False)
    current_event_id = Column(String(128), nullable=True)
    current_event_provider = Column(String(64), nullable=True)
    current_event_type = Column(String(128), nullable=True)
    
    processed_count = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)
    
    total_processing_time_ms = Column(Float, default=0.0, nullable=False)
    average_duration_ms = Column(Float, default=0.0, nullable=False)
    
    last_heartbeat = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    started_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
