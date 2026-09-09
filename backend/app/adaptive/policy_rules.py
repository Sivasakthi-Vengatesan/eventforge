from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Tuple, Optional
from backend.app.adaptive.system_state import SystemState

class SystemMode:
    NORMAL = "NORMAL"
    PRESSURE = "PRESSURE"
    DEGRADED = "DEGRADED"
    RECOVERY = "RECOVERY"

@dataclass
class PolicyThresholds:
    queue_pressure_depth: int = 50
    queue_growth_rate_limit: float = 20.0
    p95_latency_limit_ms: float = 400.0
    
    http_429_degraded_threshold: float = 0.15
    error_rate_degraded_threshold: float = 0.20
    
    recovery_error_rate_max: float = 0.05
    recovery_sustained_seconds: float = 8.0
    
    normal_queue_depth_max: int = 20
    normal_p95_latency_max: float = 200.0

@dataclass
class TransitionDecision:
    should_transition: bool
    new_mode: str
    reason: str
    triggering_metric: str
    observed_value: float
    threshold: float
    action_summary: str

class PolicyRules:
    def __init__(self, thresholds: Optional[PolicyThresholds] = None):
        self.thresholds = thresholds or PolicyThresholds()
        self._recovery_started_at: Optional[datetime] = None

    def evaluate(self, state: SystemState) -> TransitionDecision:
        current = state.current_mode
        t = self.thresholds

        # Rule 1: Check for DEGRADED triggers (Highest Priority: Downstream Health)
        if state.http_429_rate >= t.http_429_degraded_threshold:
            if current != SystemMode.DEGRADED:
                return TransitionDecision(
                    should_transition=True,
                    new_mode=SystemMode.DEGRADED,
                    reason=f"Downstream HTTP 429 rate ({round(state.http_429_rate * 100, 1)}%) exceeded critical limit ({round(t.http_429_degraded_threshold * 100, 1)}%)",
                    triggering_metric="http_429_rate",
                    observed_value=state.http_429_rate,
                    threshold=t.http_429_degraded_threshold,
                    action_summary="Reduce worker concurrency to min, throttle LOW priority, increase retry backoff to 8s"
                )
        
        if state.circuit_breaker_state == "OPEN":
            if current != SystemMode.DEGRADED:
                return TransitionDecision(
                    should_transition=True,
                    new_mode=SystemMode.DEGRADED,
                    reason="Downstream Circuit Breaker tripped to OPEN state due to consecutive service failures",
                    triggering_metric="circuit_breaker_state",
                    observed_value=1.0,
                    threshold=0.0,
                    action_summary="Halt downstream calls, apply backpressure, queue events for half-open probe"
                )

        if state.error_rate >= t.error_rate_degraded_threshold and state.queue_depth > 5:
            if current != SystemMode.DEGRADED:
                return TransitionDecision(
                    should_transition=True,
                    new_mode=SystemMode.DEGRADED,
                    reason=f"Downstream failure rate ({round(state.error_rate * 100, 1)}%) exceeded threshold ({round(t.error_rate_degraded_threshold * 100, 1)}%)",
                    triggering_metric="error_rate",
                    observed_value=state.error_rate,
                    threshold=t.error_rate_degraded_threshold,
                    action_summary="Isolate downstream, reduce dispatch rate, prioritize critical reconciliation"
                )

        # Rule 2: Handling transitions from DEGRADED -> RECOVERY
        if current == SystemMode.DEGRADED:
            # Check if health metrics have improved
            if state.http_429_rate < 0.05 and state.error_rate < t.recovery_error_rate_max and state.circuit_breaker_state != "OPEN":
                now = datetime.now(timezone.utc)
                if self._recovery_started_at is None:
                    self._recovery_started_at = now
                
                sustained_duration = (now - self._recovery_started_at).total_seconds()
                if sustained_duration >= t.recovery_sustained_seconds:
                    self._recovery_started_at = None
                    return TransitionDecision(
                        should_transition=True,
                        new_mode=SystemMode.RECOVERY,
                        reason=f"Downstream health sustained for {round(sustained_duration, 1)}s with 0% 429s and <5% errors",
                        triggering_metric="sustained_healthy_duration",
                        observed_value=sustained_duration,
                        threshold=t.recovery_sustained_seconds,
                        action_summary="Gradually restore concurrency to 4 workers, test downstream with controlled probe rates"
                    )
            else:
                self._recovery_started_at = None
            
            return TransitionDecision(should_transition=False, new_mode=current, reason="", triggering_metric="", observed_value=0, threshold=0, action_summary="")

        # Rule 3: Handling transitions from RECOVERY -> NORMAL
        if current == SystemMode.RECOVERY:
            if state.queue_depth <= t.normal_queue_depth_max and state.p95_latency_ms <= t.normal_p95_latency_max and state.error_rate < 0.02:
                return TransitionDecision(
                    should_transition=True,
                    new_mode=SystemMode.NORMAL,
                    reason=f"Backlog drained (queue depth {state.queue_depth} <= {t.normal_queue_depth_max}) and latency normalized",
                    triggering_metric="queue_depth",
                    observed_value=float(state.queue_depth),
                    threshold=float(t.normal_queue_depth_max),
                    action_summary="Restore standard 4 workers, disable throttling, normalize retry schedules"
                )
            return TransitionDecision(should_transition=False, new_mode=current, reason="", triggering_metric="", observed_value=0, threshold=0, action_summary="")

        # Rule 4: Check for PRESSURE triggers
        if state.queue_depth >= t.queue_pressure_depth or state.queue_growth_rate > t.queue_growth_rate_limit or state.p95_latency_ms >= t.p95_latency_limit_ms:
            if current != SystemMode.PRESSURE:
                reason_detail = []
                metric_name = "queue_depth"
                metric_val = float(state.queue_depth)
                metric_thresh = float(t.queue_pressure_depth)
                
                if state.queue_depth >= t.queue_pressure_depth:
                    reason_detail.append(f"Queue depth ({state.queue_depth}) >= {t.queue_pressure_depth}")
                if state.queue_growth_rate > t.queue_growth_rate_limit:
                    reason_detail.append(f"Queue growth ({round(state.queue_growth_rate, 1)}/s) > {t.queue_growth_rate_limit}/s")
                    metric_name = "queue_growth_rate"
                    metric_val = state.queue_growth_rate
                    metric_thresh = t.queue_growth_rate_limit
                if state.p95_latency_ms >= t.p95_latency_limit_ms:
                    reason_detail.append(f"P95 latency ({round(state.p95_latency_ms, 1)}ms) >= {t.p95_latency_limit_ms}ms")
                    metric_name = "p95_latency_ms"
                    metric_val = state.p95_latency_ms
                    metric_thresh = t.p95_latency_limit_ms

                return TransitionDecision(
                    should_transition=True,
                    new_mode=SystemMode.PRESSURE,
                    reason="; ".join(reason_detail),
                    triggering_metric=metric_name,
                    observed_value=metric_val,
                    threshold=metric_thresh,
                    action_summary="Scale worker concurrency from 4 to 8, prioritize CRITICAL/HIGH events, buffer batch-safe LOW work"
                )

        # Rule 5: Handling transitions from PRESSURE -> NORMAL
        if current == SystemMode.PRESSURE:
            if state.queue_depth <= t.normal_queue_depth_max and state.p95_latency_ms <= t.normal_p95_latency_max:
                return TransitionDecision(
                    should_transition=True,
                    new_mode=SystemMode.NORMAL,
                    reason=f"Queue backlog normalized ({state.queue_depth} <= {t.normal_queue_depth_max}) and P95 latency stable ({round(state.p95_latency_ms, 1)}ms)",
                    triggering_metric="queue_depth",
                    observed_value=float(state.queue_depth),
                    threshold=float(t.normal_queue_depth_max),
                    action_summary="Scale concurrency back to standard 4 workers, release buffered batches"
                )

        return TransitionDecision(
            should_transition=False,
            new_mode=current,
            reason="",
            triggering_metric="",
            observed_value=0,
            threshold=0,
            action_summary=""
        )
