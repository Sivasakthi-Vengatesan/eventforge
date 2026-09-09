import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from backend.app.adaptive.priority_router import EventPriority, PriorityRouter
from backend.app.adaptive.policy_rules import SystemMode

class BackpressureManager:
    """Manages adaptive backpressure, delays, throttling, and batching buffers."""

    def __init__(self):
        self._delayed_count: int = 0
        self._throttled_count: int = 0
        self._batched_count: int = 0
        self._batch_buffer: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = asyncio.Lock()

    @property
    def delayed_count(self) -> int:
        return self._delayed_count

    @property
    def throttled_count(self) -> int:
        return self._throttled_count

    @property
    def batched_count(self) -> int:
        return self._batched_count

    def should_delay(self, priority: str, mode: str) -> Tuple[bool, float]:
        """Determines if an event should be delayed based on current mode and priority."""
        if priority == EventPriority.CRITICAL:
            return False, 0.0

        if mode == SystemMode.DEGRADED:
            if priority == EventPriority.HIGH:
                return False, 0.0  # Protect high/critical
            if priority == EventPriority.NORMAL:
                self._delayed_count += 1
                return True, 3.0   # Delay normal by 3s
            if priority == EventPriority.LOW:
                self._throttled_count += 1
                return True, 8.0   # Throttle low by 8s

        elif mode == SystemMode.PRESSURE:
            if priority == EventPriority.LOW:
                self._delayed_count += 1
                return True, 2.0   # Delay low by 2s

        return False, 0.0

    async def add_to_batch_buffer(self, provider: str, event_type: str, event_data: Dict[str, Any], max_batch_size: int = 25) -> Optional[List[Dict[str, Any]]]:
        """Buffers batch-safe events and returns batch when ready."""
        key = f"{provider}:{event_type}"
        async with self._lock:
            if key not in self._batch_buffer:
                self._batch_buffer[key] = []
            
            self._batch_buffer[key].append(event_data)
            self._batched_count += 1

            if len(self._batch_buffer[key]) >= max_batch_size:
                batch = self._batch_buffer[key]
                self._batch_buffer[key] = []
                return batch
            
            return None

    async def flush_all_batches(self) -> List[List[Dict[str, Any]]]:
        """Flushes all buffered events when pressure normalizes."""
        async with self._lock:
            flushed = []
            for key, items in list(self._batch_buffer.items()):
                if items:
                    flushed.append(items)
                    self._batch_buffer[key] = []
            return flushed
