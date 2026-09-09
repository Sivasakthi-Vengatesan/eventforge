from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class WebhookIngestResponse(BaseModel):
    status: str = Field(default="ACCEPTED", description="Ingestion status (ACCEPTED or DUPLICATE)")
    event_id: str
    provider: str
    event_type: str
    received_at: str
    message: str

class GenericWebhookPayload(BaseModel):
    event_id: Optional[str] = None
    event_type: Optional[str] = "generic.event"
    data: Optional[Dict[str, Any]] = None
    timestamp: Optional[int] = None
