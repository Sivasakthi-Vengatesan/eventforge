import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger("rheos.circuit_breaker")

class CircuitBreakerOpenException(Exception):
    pass

class CircuitBreaker:
    """Standard distributed reliability circuit breaker with CLOSED, OPEN, and HALF_OPEN states."""

    def __init__(
        self,
        service_name: str = "downstream-verification",
        failure_threshold: float = 0.30,
        consecutive_failures_limit: int = 4,
        cooldown_seconds: float = 10.0,
        half_open_success_needed: int = 2
    ):
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.consecutive_failures_limit = consecutive_failures_limit
        self.cooldown_seconds = cooldown_seconds
        self.half_open_success_needed = half_open_success_needed

        self._state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self._consecutive_failures: int = 0
        self._total_requests: int = 0
        self._total_failures: int = 0
        self._half_open_successes: int = 0
        self._opened_at: Optional[datetime] = None
        self._last_state_change: datetime = datetime.now(timezone.utc)
        self._simulated_fault: Optional[str] = None
        self._lock = asyncio.Lock()

    @property
    def state(self) -> str:
        # Check if OPEN cooldown has expired and should transition to HALF_OPEN
        if self._state == "OPEN" and self._opened_at:
            elapsed = (datetime.now(timezone.utc) - self._opened_at).total_seconds()
            if elapsed >= self.cooldown_seconds:
                self._state = "HALF_OPEN"
                self._half_open_successes = 0
                self._last_state_change = datetime.now(timezone.utc)
                logger.info(f"Circuit Breaker [{self.service_name}]: Cooldown expired -> HALF_OPEN (Probing downstream)")
        return self._state

    def set_simulated_fault(self, fault: Optional[str]):
        """Sets a runtime simulated fault like 429, 500, timeout."""
        self._simulated_fault = fault
        logger.info(f"Circuit Breaker [{self.service_name}]: Simulated fault set to {fault}")

    @property
    def simulated_fault(self) -> Optional[str]:
        return self._simulated_fault

    async def can_execute(self) -> bool:
        """Returns True if request is allowed to proceed; False or raises if circuit is OPEN."""
        current_state = self.state
        if current_state == "OPEN":
            return False
        return True

    async def record_result(self, is_success: bool, status_code: Optional[int] = None):
        """Records execution outcome and updates state machine."""
        async with self._lock:
            self._total_requests += 1
            now = datetime.now(timezone.utc)

            if is_success:
                if self._state == "HALF_OPEN":
                    self._half_open_successes += 1
                    if self._half_open_successes >= self.half_open_success_needed:
                        self._state = "CLOSED"
                        self._consecutive_failures = 0
                        self._opened_at = None
                        self._last_state_change = now
                        logger.info(f"Circuit Breaker [{self.service_name}]: Probe passed ({self._half_open_successes} OK) -> CLOSED")
                else:
                    self._consecutive_failures = max(0, self._consecutive_failures - 1)
            else:
                self._total_failures += 1
                self._consecutive_failures += 1

                if self._state == "HALF_OPEN":
                    # Probe failed: immediate trip back to OPEN
                    self._state = "OPEN"
                    self._opened_at = now
                    self._last_state_change = now
                    logger.warning(f"Circuit Breaker [{self.service_name}]: Half-open probe failed -> Trip back to OPEN")

                elif self._state == "CLOSED":
                    if self._consecutive_failures >= self.consecutive_failures_limit:
                        self._state = "OPEN"
                        self._opened_at = now
                        self._last_state_change = now
                        logger.error(f"Circuit Breaker [{self.service_name}]: {self._consecutive_failures} consecutive failures -> Trip to OPEN")

    def get_status(self) -> Dict[str, Any]:
        return {
            "service_name": self.service_name,
            "state": self.state,
            "failure_threshold": self.failure_threshold,
            "cooldown_seconds": int(self.cooldown_seconds),
            "consecutive_failures": self._consecutive_failures,
            "total_requests": self._total_requests,
            "total_failures": self._total_failures,
            "last_state_change": self._last_state_change.isoformat(),
            "simulated_fault": self._simulated_fault,
        }

# Global singleton
_circuit_breaker_instance: Optional[CircuitBreaker] = None

def get_circuit_breaker() -> CircuitBreaker:
    global _circuit_breaker_instance
    if _circuit_breaker_instance is None:
        _circuit_breaker_instance = CircuitBreaker()
    return _circuit_breaker_instance
