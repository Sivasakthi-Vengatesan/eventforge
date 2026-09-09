import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.adaptive.system_state import SystemStateManager, SystemState
from backend.app.adaptive.policy_rules import PolicyRules, SystemMode, TransitionDecision
from backend.app.adaptive.priority_router import PriorityRouter, EventPriority
from backend.app.adaptive.backpressure import BackpressureManager
from backend.app.adaptive.controller import AdaptiveController
from backend.app.database.connection import get_db_context
from backend.app.models.event import PolicyDecisionRecord

logger = logging.getLogger("eventforge.adaptive.engine")

class AdaptivePolicyEngine:
    """Core Adaptive Event Policy Engine observing telemetry and dynamically governing pipeline behavior."""

    def __init__(self):
        self.state_manager = SystemStateManager()
        self.rules = PolicyRules()
        self.priority_router = PriorityRouter()
        self.backpressure = BackpressureManager()
        self.controller = AdaptiveController()
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._ws_manager = None
        self._worker_manager = None
        self._decisions_cache: List[Dict[str, Any]] = []

    def set_ws_manager(self, ws_manager):
        self._ws_manager = ws_manager

    def set_worker_manager(self, worker_manager):
        self._worker_manager = worker_manager

    @property
    def current_mode(self) -> str:
        return self.state_manager.get_state().current_mode

    @property
    def system_state(self) -> SystemState:
        return self.state_manager.get_state()

    def get_decisions_history(self) -> List[Dict[str, Any]]:
        return list(reversed(self._decisions_cache[-50:]))

    async def start(self):
        """Starts the continuous background evaluation loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._evaluation_loop())
        logger.info("Adaptive Policy Engine started.")

    async def stop(self):
        """Stops the evaluation loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Adaptive Policy Engine stopped.")

    async def _evaluation_loop(self):
        """Periodically evaluates state and triggers deterministic transitions."""
        while self._running:
            try:
                await self.evaluate_once()
            except Exception as e:
                logger.error(f"Error in policy evaluation loop: {e}", exc_info=True)
            await asyncio.sleep(1.5)

    async def evaluate_once(self):
        state = self.state_manager.get_state()
        state.delayed_events_count = self.backpressure.delayed_count
        state.throttled_events_count = self.backpressure.throttled_count
        state.batched_events_count = self.backpressure.batched_count

        decision: TransitionDecision = self.rules.evaluate(state)

        if decision.should_transition and decision.new_mode != state.current_mode:
            await self._execute_transition(decision)

    async def manual_override(self, new_mode: str, reason: str = "Manual operator override") -> Dict[str, Any]:
        """Allows explicit administrative transition for demonstration and chaos drills."""
        state = self.state_manager.get_state()
        decision = TransitionDecision(
            should_transition=True,
            new_mode=new_mode,
            reason=reason,
            triggering_metric="manual_override",
            observed_value=1.0,
            threshold=1.0,
            action_summary=f"Operator manually forced system state to {new_mode}"
        )
        return await self._execute_transition(decision)

    async def _execute_transition(self, decision: TransitionDecision) -> Dict[str, Any]:
        prev_mode = self.state_manager.get_state().current_mode
        self.state_manager.get_state().current_mode = decision.new_mode

        # Execute operational adjustments
        actions = await self.controller.apply_policy(decision, self._worker_manager)

        # Log decision into database
        decision_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "previous_mode": prev_mode,
            "new_mode": decision.new_mode,
            "reason": decision.reason,
            "triggering_metric": decision.triggering_metric,
            "observed_value": round(decision.observed_value, 3),
            "threshold": round(decision.threshold, 3),
            "action": decision.action_summary,
            "old_parameter": prev_mode,
            "new_parameter": decision.new_mode,
        }

        self._decisions_cache.append(decision_data)

        # Persist to DB asynchronously
        asyncio.create_task(self._persist_decision(decision_data))

        # Broadcast policy transition via WebSockets
        if self._ws_manager:
            try:
                await self._ws_manager.broadcast({
                    "type": "POLICY_TRANSITION",
                    "data": {
                        "previous_mode": prev_mode,
                        "new_mode": decision.new_mode,
                        "reason": decision.reason,
                        "actions": actions,
                        "timestamp": decision_data["timestamp"]
                    }
                })
            except Exception as e:
                logger.error(f"Failed to broadcast policy transition: {e}")

        logger.info(f"POLICY TRANSITION: {prev_mode} -> {decision.new_mode} | Reason: {decision.reason}")
        return decision_data

    async def _persist_decision(self, data: Dict[str, Any]):
        try:
            async with get_db_context() as db:
                record = PolicyDecisionRecord(
                    previous_mode=data["previous_mode"],
                    new_mode=data["new_mode"],
                    reason=data["reason"],
                    triggering_metric=data["triggering_metric"],
                    observed_value=data["observed_value"],
                    threshold=data["threshold"],
                    action=data["action"],
                    old_parameter=data.get("old_parameter"),
                    new_parameter=data.get("new_parameter")
                )
                db.add(record)
                await db.commit()
        except Exception as e:
            logger.error(f"Error persisting policy decision: {e}")

# Global singleton
_policy_engine_instance: Optional[AdaptivePolicyEngine] = None

def get_policy_engine() -> AdaptivePolicyEngine:
    global _policy_engine_instance
    if _policy_engine_instance is None:
        _policy_engine_instance = AdaptivePolicyEngine()
    return _policy_engine_instance
