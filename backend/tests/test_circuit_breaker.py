import pytest
import asyncio
from backend.app.services.circuit_breaker import CircuitBreaker

@pytest.mark.asyncio
async def test_circuit_breaker_trip_and_cooldown():
    cb = CircuitBreaker(
        service_name="test-service",
        consecutive_failures_limit=3,
        cooldown_seconds=0.2,
        half_open_success_needed=1
    )

    assert cb.state == "CLOSED"
    assert await cb.can_execute() is True

    # Record 3 failures to trip the circuit
    await cb.record_result(False, status_code=500)
    await cb.record_result(False, status_code=500)
    await cb.record_result(False, status_code=500)

    # Circuit should now be OPEN
    assert cb.state == "OPEN"
    assert await cb.can_execute() is False

    # Wait for cooldown to transition to HALF_OPEN
    await asyncio.sleep(0.25)
    assert cb.state == "HALF_OPEN"
    assert await cb.can_execute() is True

    # Successful probe restores to CLOSED
    await cb.record_result(True, status_code=200)
    assert cb.state == "CLOSED"
    assert await cb.can_execute() is True

@pytest.mark.asyncio
async def test_circuit_breaker_half_open_failure_re_trip():
    cb = CircuitBreaker(
        service_name="test-re-trip",
        consecutive_failures_limit=2,
        cooldown_seconds=0.1,
        half_open_success_needed=1
    )

    await cb.record_result(False, status_code=500)
    await cb.record_result(False, status_code=500)
    assert cb.state == "OPEN"

    await asyncio.sleep(0.15)
    assert cb.state == "HALF_OPEN"

    # Failed probe immediately trips back to OPEN
    await cb.record_result(False, status_code=500)
    assert cb.state == "OPEN"
