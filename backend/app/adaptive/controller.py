import logging
from typing import Dict, Any, Optional
from backend.app.adaptive.policy_rules import SystemMode, TransitionDecision

logger = logging.getLogger("rheos.adaptive.controller")

class AdaptiveController:
    """Executes actions dictated by the Adaptive Policy Engine."""

    def __init__(self, min_workers: int = 2, max_workers: int = 8, default_workers: int = 4):
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.default_workers = default_workers
        self.current_target_workers = default_workers
        self.current_retry_multiplier = 1.0
        self.current_mode = SystemMode.NORMAL

    async def apply_policy(self, decision: TransitionDecision, worker_manager=None) -> Dict[str, Any]:
        """Applies configuration shifts based on mode transition."""
        self.current_mode = decision.new_mode
        actions_taken = {}

        if decision.new_mode == SystemMode.PRESSURE:
            # Scale up concurrency within bounds to drain pressure
            self.current_target_workers = self.max_workers  # e.g. 8
            self.current_retry_multiplier = 1.0
            actions_taken["worker_concurrency"] = f"{self.default_workers} -> {self.max_workers}"
            actions_taken["backpressure"] = "Delaying LOW priority events by 2s"

        elif decision.new_mode == SystemMode.DEGRADED:
            # Scale down concurrency to protect downstream dependency from retry storms
            self.current_target_workers = self.min_workers  # e.g. 2
            self.current_retry_multiplier = 4.0            # Increase backoff
            actions_taken["worker_concurrency"] = f"Scaled down to {self.min_workers}"
            actions_taken["retry_backoff"] = "Base delay multiplied 4x (8s)"
            actions_taken["throttling"] = "Throttling LOW priority, protecting CRITICAL/HIGH"

        elif decision.new_mode == SystemMode.RECOVERY:
            # Stepwise ramp up
            self.current_target_workers = self.default_workers  # 4
            self.current_retry_multiplier = 1.5
            actions_taken["worker_concurrency"] = f"Ramping to {self.default_workers}"
            actions_taken["retry_backoff"] = "Normalized to 1.5x"

        elif decision.new_mode == SystemMode.NORMAL:
            self.current_target_workers = self.default_workers
            self.current_retry_multiplier = 1.0
            actions_taken["worker_concurrency"] = f"Restored to {self.default_workers}"
            actions_taken["retry_backoff"] = "Normal (1.0x)"

        if worker_manager is not None:
            try:
                await worker_manager.set_target_concurrency(self.current_target_workers)
            except Exception as e:
                logger.error(f"Error applying worker scale: {e}")

        logger.info(f"Policy applied: {decision.new_mode} -> {actions_taken}")
        return actions_taken
