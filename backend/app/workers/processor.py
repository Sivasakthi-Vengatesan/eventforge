import time
from typing import Dict, Any, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.event import Event, EventAttempt, EventStatus
from backend.app.services.retry import retry_service
from backend.app.services.downstream_mock import get_downstream_service
from backend.app.adaptive.policy_engine import get_policy_engine
from backend.app.core.logging import logger

class EventProcessor:
    @staticmethod
    async def process_event(
        db: AsyncSession,
        event: Event,
        worker_id: str,
    ) -> Tuple[bool, Optional[str], Optional[int], bool]:
        """
        Executes downstream verification using DownstreamService and CircuitBreaker.
        Returns: (is_success, error_message, status_code, is_retryable)
        """
        start_time = time.perf_counter()
        attempt_number = event.retry_count + 1
        provider = event.provider.lower()
        downstream = get_downstream_service()
        policy_engine = get_policy_engine()
        current_mode = policy_engine.current_mode

        # Check for mock fault injected in headers
        force_fault = None
        if event.headers and isinstance(event.headers, dict):
            force_fault = event.headers.get("x-mock-fault")

        # Execute downstream verification
        is_success, status_code, response_data, duration_ms = await downstream.verify_and_process(
            provider=provider,
            event_type=event.event_type,
            payload=event.payload,
            force_fault=force_fault
        )

        error_msg = None
        is_retryable = True

        if not is_success:
            error_msg = response_data.get("error", f"Downstream returned HTTP {status_code}")
            is_retryable = retry_service.is_retryable(status_code, error_msg)

        # Record attempt with policy mode
        attempt = EventAttempt(
            event_id=event.event_id,
            provider=event.provider,
            attempt_number=attempt_number,
            worker_id=worker_id,
            status="SUCCESS" if is_success else "FAILED",
            policy_mode=current_mode,
            duration_ms=round(duration_ms, 2),
            error_message=error_msg,
            response_status_code=status_code,
            is_retryable=is_retryable
        )
        db.add(attempt)

        return is_success, error_msg, status_code, is_retryable

event_processor = EventProcessor()

