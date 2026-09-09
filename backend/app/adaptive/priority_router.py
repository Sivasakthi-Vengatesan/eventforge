from typing import Dict, Any, Optional

class EventPriority:
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"

class PriorityRouter:
    """Classifies incoming webhooks and determines dispatch order and batching eligibility."""

    CRITICAL_EVENT_TYPES = {
        "payment.failed",
        "charge.failed",
        "security.alert",
        "security.breach",
        "account.suspended",
        "charge.dispute.created",
        "deployment.failed",
    }

    HIGH_EVENT_TYPES = {
        "payment.success",
        "payment.captured",
        "payment_intent.succeeded",
        "refund.created",
        "refund.processed",
        "order.paid",
        "subscription.renewed",
        "release.published",
    }

    NORMAL_EVENT_TYPES = {
        "order.updated",
        "order.created",
        "customer.created",
        "push",
        "pull_request",
        "issues",
        "issue_comment",
        "deployment.created",
        "generic.event",
    }

    LOW_EVENT_TYPES = {
        "analytics.event",
        "telemetry.ping",
        "page_view",
        "user.heartbeat",
        "audit.ping",
        "log.trace",
    }

    BATCH_SAFE_TYPES = {
        "analytics.event",
        "telemetry.ping",
        "page_view",
        "audit.ping",
    }

    @classmethod
    def classify(cls, provider: str, event_type: str, payload: Optional[Dict[str, Any]] = None) -> str:
        """Determines event priority based on explicit payload flags, event type, and provider."""
        if payload and isinstance(payload, dict):
            if "priority" in payload and payload["priority"] in [
                EventPriority.CRITICAL, EventPriority.HIGH, EventPriority.NORMAL, EventPriority.LOW
            ]:
                return payload["priority"]
            if payload.get("is_urgent") is True:
                return EventPriority.CRITICAL

        e_type = event_type.lower()
        if e_type in cls.CRITICAL_EVENT_TYPES:
            return EventPriority.CRITICAL
        if e_type in cls.HIGH_EVENT_TYPES:
            return EventPriority.HIGH
        if e_type in cls.LOW_EVENT_TYPES:
            return EventPriority.LOW
        
        return EventPriority.NORMAL

    @classmethod
    def is_batch_safe(cls, event_type: str) -> bool:
        """Returns True if the event type can be batched during pressure or degraded modes."""
        return event_type.lower() in cls.BATCH_SAFE_TYPES

    @classmethod
    def get_priority_weight(cls, priority: str) -> int:
        """Returns integer weight for priority scheduling (higher = processed first)."""
        weights = {
            EventPriority.CRITICAL: 100,
            EventPriority.HIGH: 50,
            EventPriority.NORMAL: 20,
            EventPriority.LOW: 5,
        }
        return weights.get(priority, 20)
