from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from backend.app.database.base import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class DeadLetterEvent(Base):
    __tablename__ = "dead_letter_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dlq_id = Column(String(128), unique=True, index=True, nullable=False)
    event_id = Column(String(128), index=True, nullable=False)
    provider = Column(String(64), nullable=False)
    event_type = Column(String(128), nullable=False)
    payload = Column(JSON, nullable=False)
    headers = Column(JSON, nullable=True)
    failure_reason = Column(Text, nullable=False)
    error_trace = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    is_resolved = Column(Boolean, default=False, nullable=False)
