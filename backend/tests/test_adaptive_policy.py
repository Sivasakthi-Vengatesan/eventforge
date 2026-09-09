import pytest
from backend.app.adaptive.system_state import SystemState, SystemStateManager
from backend.app.adaptive.policy_rules import PolicyRules, SystemMode, PolicyThresholds
from backend.app.adaptive.priority_router import PriorityRouter, EventPriority
from backend.app.adaptive.backpressure import BackpressureManager
from backend.app.adaptive.controller import AdaptiveController

def test_priority_router_classification():
    assert PriorityRouter.classify("stripe", "payment.failed") == EventPriority.CRITICAL
    assert PriorityRouter.classify("stripe", "security.alert") == EventPriority.CRITICAL
    assert PriorityRouter.classify("stripe", "payment_intent.succeeded") == EventPriority.HIGH
    assert PriorityRouter.classify("github", "push") == EventPriority.NORMAL
    assert PriorityRouter.classify("generic", "analytics.event") == EventPriority.LOW

def test_priority_router_batch_safety():
    assert PriorityRouter.is_batch_safe("analytics.event") is True
    assert PriorityRouter.is_batch_safe("telemetry.ping") is True
    assert PriorityRouter.is_batch_safe("payment.failed") is False
    assert PriorityRouter.is_batch_safe("payment_intent.succeeded") is False

def test_policy_rules_normal_to_pressure_transition():
    rules = PolicyRules(PolicyThresholds(queue_pressure_depth=50, p95_latency_limit_ms=400.0))
    state = SystemState(current_mode=SystemMode.NORMAL, queue_depth=75, p95_latency_ms=120.0)
    
    decision = rules.evaluate(state)
    assert decision.should_transition is True
    assert decision.new_mode == SystemMode.PRESSURE
    assert "Queue depth" in decision.reason

def test_policy_rules_pressure_to_degraded_on_429():
    rules = PolicyRules(PolicyThresholds(http_429_degraded_threshold=0.15))
    state = SystemState(current_mode=SystemMode.PRESSURE, http_429_rate=0.25)
    
    decision = rules.evaluate(state)
    assert decision.should_transition is True
    assert decision.new_mode == SystemMode.DEGRADED
    assert "HTTP 429" in decision.reason

def test_adaptive_backpressure_delays():
    bp = BackpressureManager()
    
    # Critical events should NEVER be delayed in any mode
    should_delay, sec = bp.should_delay(EventPriority.CRITICAL, SystemMode.DEGRADED)
    assert should_delay is False
    assert sec == 0.0

    # Low priority should be delayed in PRESSURE mode
    should_delay, sec = bp.should_delay(EventPriority.LOW, SystemMode.PRESSURE)
    assert should_delay is True
    assert sec == 2.0

    # Normal priority should be delayed in DEGRADED mode
    should_delay, sec = bp.should_delay(EventPriority.NORMAL, SystemMode.DEGRADED)
    assert should_delay is True
    assert sec == 3.0

@pytest.mark.asyncio
async def test_adaptive_controller_actions():
    controller = AdaptiveController(min_workers=2, max_workers=8, default_workers=4)
    
    from backend.app.adaptive.policy_rules import TransitionDecision
    decision_pressure = TransitionDecision(
        should_transition=True,
        new_mode=SystemMode.PRESSURE,
        reason="Queue backlog",
        triggering_metric="queue_depth",
        observed_value=80.0,
        threshold=50.0,
        action_summary="Scale workers up"
    )
    
    actions = await controller.apply_policy(decision_pressure)
    assert controller.current_target_workers == 8
    assert "worker_concurrency" in actions

    decision_degraded = TransitionDecision(
        should_transition=True,
        new_mode=SystemMode.DEGRADED,
        reason="429 rate",
        triggering_metric="http_429_rate",
        observed_value=0.30,
        threshold=0.15,
        action_summary="Scale down and increase backoff"
    )
    
    actions_deg = await controller.apply_policy(decision_degraded)
    assert controller.current_target_workers == 2
    assert controller.current_retry_multiplier == 4.0
