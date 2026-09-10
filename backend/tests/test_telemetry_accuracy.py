import asyncio
import pytest
import httpx
from backend.app.main import app
from backend.app.monitoring.metrics_collector import MetricsCollector
from backend.app.adaptive.policy_rules import PolicyRules, TransitionDecision
from backend.app.adaptive.system_state import SystemStateManager
from backend.app.adaptive.policy_engine import AdaptivePolicyEngine
from backend.app.monitoring.websocket_manager import WebSocketManager

@pytest.mark.asyncio
async def test_truthful_telemetry_and_429_tracking():
    """
    Verifies that MetricsCollector accurately computes error rate, 429 rate,
    and retry rate based on real execution data without random or fake values.
    """
    mc = MetricsCollector()
    
    # Record 8 successes, 2 failures (both 429)
    for _ in range(8):
        mc.record_event_completion(duration_ms=45.0, is_success=True, status_code=200)
    for _ in range(2):
        mc.record_event_completion(duration_ms=150.0, is_success=False, status_code=429)
        mc.record_retry()

    assert mc.get_error_rate() == 0.20
    assert mc.get_429_rate() == 0.20
    assert mc.get_retry_rate() > 0.0

    percentiles = mc.calculate_percentiles()
    assert percentiles["p50"] > 0
    assert percentiles["p95"] >= percentiles["p50"]

@pytest.mark.asyncio
async def test_adaptive_policy_transition_and_websocket_broadcast():
    """
    Verifies that PolicyEngine transitions deterministically upon 429 threshold breach
    and broadcasts the POLICY_TRANSITION WebSocket event with full metadata.
    """
    engine = AdaptivePolicyEngine()
    
    # Mock WebSocket manager to intercept broadcast
    broadcasted_messages = []
    class MockWSManager:
        async def broadcast(self, message_type: str, data: dict):
            broadcasted_messages.append({"type": message_type, "data": data})

    mock_ws = MockWSManager()
    engine.set_ws_manager(mock_ws)

    # Simulate 429 breach (rate > 0.15)
    engine.state_manager.update_metrics(
        queue_depth=10,
        ingestion_rate=50.0,
        processing_rate=45.0,
        worker_utilization=0.8,
        p50=30.0,
        p95=250.0,
        p99=400.0,
        error_rate=0.25,
        retry_rate=0.25,
        http_429_rate=0.25,
        active_workers=4
    )

    await engine.evaluate_once()
    assert engine.current_mode == "DEGRADED"

    # Verify WebSocket broadcast payload structure
    assert len(broadcasted_messages) == 1
    msg = broadcasted_messages[0]
    assert msg["type"] == "POLICY_TRANSITION"
    data = msg["data"]
    assert data["previous_mode"] == "NORMAL"
    assert data["new_mode"] == "DEGRADED"
    assert "reason" in data
    assert "triggering_metric" in data
    assert "timestamp" in data

@pytest.mark.asyncio
async def test_health_check_endpoints_truthful():
    """
    Verifies that /health, /health/redis, and /health/database return
    truthful status and component metadata.
    """
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Main Health
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        health_data = resp.json()
        assert health_data["status"] in ["HEALTHY", "DEGRADED"]
        assert "HEALTHY" in health_data["database"]

        # 2. Redis Health
        redis_resp = await client.get("/api/v1/health/redis")
        assert redis_resp.status_code == 200
        redis_data = redis_resp.json()
        assert "status" in redis_data
        assert "mode" in redis_data

        # 3. Database Health
        db_resp = await client.get("/api/v1/health/database")
        assert db_resp.status_code == 200
        db_data = db_resp.json()
        assert db_data["status"] == "HEALTHY"
        assert db_data["connected"] is True
