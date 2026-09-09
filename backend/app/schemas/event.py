from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict

class EventAttemptSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: str
    provider: str
    attempt_number: int
    worker_id: str
    status: str
    policy_mode: Optional[str] = "NORMAL"
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    error_message: Optional[str] = None
    response_status_code: Optional[int] = None
    is_retryable: bool

class EventSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: str
    provider: str
    event_type: str
    priority: str = "NORMAL"
    payload: Dict[str, Any]
    headers: Optional[Dict[str, Any]] = None
    status: str
    current_mode: str = "NORMAL"
    current_policy: Optional[Dict[str, Any]] = None
    retry_count: int
    max_retries: int
    received_at: datetime
    queued_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_duration_ms: Optional[float] = None
    error_message: Optional[str] = None
    last_error_type: Optional[str] = None
    is_duplicate: bool
    duplicate_count: int

class EventDetailSchema(EventSchema):
    attempts: List[EventAttemptSchema] = []

class EventListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[EventSchema]

