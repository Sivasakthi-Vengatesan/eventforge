import asyncio
import random
import time
import logging
from typing import Dict, Any, Tuple, Optional
from backend.app.services.circuit_breaker import get_circuit_breaker, CircuitBreakerOpenException

logger = logging.getLogger("eventforge.downstream_mock")

class DownstreamService:
    """Simulates real downstream API interactions with circuit breaker protection and fault injection."""

    def __init__(self):
        self.circuit_breaker = get_circuit_breaker()
        self.default_latency_range_ms = (15, 65)

    async def verify_and_process(
        self,
        provider: str,
        event_type: str,
        payload: Dict[str, Any],
        force_fault: Optional[str] = None
    ) -> Tuple[bool, int, Dict[str, Any], float]:
        """
        Executes downstream verification.
        Returns: (success: bool, status_code: int, response_data: dict, duration_ms: float)
        """
        start_time = time.perf_counter()

        # Step 1: Check Circuit Breaker
        if not await self.circuit_breaker.can_execute():
            duration = (time.perf_counter() - start_time) * 1000
            logger.warning("Downstream call rejected: Circuit Breaker is OPEN.")
            return False, 503, {"error": "Circuit Breaker OPEN - Downstream Unavailable"}, duration

        # Check for active simulated fault (from header, parameter, or circuit breaker setting)
        active_fault = force_fault or self.circuit_breaker.simulated_fault

        # Latency simulation
        if active_fault == "timeout":
            await asyncio.sleep(1.2)  # Simulate 1200ms timeout
            duration = (time.perf_counter() - start_time) * 1000
            await self.circuit_breaker.record_result(False, status_code=504)
            return False, 504, {"error": "Downstream Gateway Timeout (>1000ms)"}, duration
        
        elif active_fault == "high_latency":
            latency_ms = random.uniform(800, 1500)
            await asyncio.sleep(latency_ms / 1000.0)
        else:
            base_latency = random.uniform(*self.default_latency_range_ms)
            await asyncio.sleep(base_latency / 1000.0)

        duration = (time.perf_counter() - start_time) * 1000

        # Step 2: Handle fault modes
        if active_fault == "429" or active_fault == "HTTP_429" or active_fault == "rate_limit":
            await self.circuit_breaker.record_result(False, status_code=429)
            return False, 429, {"error": "Downstream Rate Limit Exceeded (HTTP 429)"}, duration

        elif active_fault == "500" or active_fault == "HTTP_500" or active_fault == "server_error":
            await self.circuit_breaker.record_result(False, status_code=500)
            return False, 500, {"error": "Internal Downstream Dependency Crash (HTTP 500)"}, duration

        elif active_fault == "503" or active_fault == "HTTP_503":
            await self.circuit_breaker.record_result(False, status_code=503)
            return False, 503, {"error": "Service Temporarily Unavailable (HTTP 503)"}, duration

        elif active_fault == "invalid_data" or active_fault == "schema_error":
            # Fatal non-retryable 400 error
            await self.circuit_breaker.record_result(True, status_code=400)  # 400 doesn't trip circuit breaker
            return False, 400, {"error": "Fatal Schema Corruption / Validation Invariant Failed"}, duration

        # Step 3: Success
        await self.circuit_breaker.record_result(True, status_code=200)
        return True, 200, {
            "verified": True,
            "provider": provider,
            "event_type": event_type,
            "processed_at": time.time(),
            "confirmation_id": f"ack_{random.randint(100000, 999999)}"
        }, duration

_downstream_instance: Optional[DownstreamService] = None

def get_downstream_service() -> DownstreamService:
    global _downstream_instance
    if _downstream_instance is None:
        _downstream_instance = DownstreamService()
    return _downstream_instance
