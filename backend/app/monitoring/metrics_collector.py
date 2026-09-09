import asyncio
import time
from collections import deque
from datetime import datetime, timezone
from typing import Dict, Any, List
import statistics
from sqlalchemy import select, func
from backend.app.database.connection import AsyncSessionLocal
from backend.app.models.event import Event, EventStatus
from backend.app.models.worker import Worker, WorkerStatus
from backend.app.models.dlq import DeadLetterEvent
from backend.app.queue.stream_manager import stream_manager
from backend.app.monitoring.websocket_manager import ws_manager
from backend.app.core.logging import logger

from backend.app.services.circuit_breaker import get_circuit_breaker
from backend.app.adaptive.policy_engine import get_policy_engine
from backend.app.models.event import EventPriority

class MetricsCollector:
    def __init__(self):
        self.recent_latencies: deque = deque(maxlen=500)
        self.processed_timestamps: deque = deque(maxlen=1000)
        self.recent_errors: deque = deque(maxlen=200)
        self.recent_429s: deque = deque(maxlen=200)
        self.is_running = False
        self._task: asyncio.Task = None

    def record_event_completion(self, duration_ms: float, is_success: bool = True, status_code: int = 200):
        now = time.time()
        self.recent_latencies.append(duration_ms)
        self.processed_timestamps.append(now)
        self.recent_errors.append(0 if is_success else 1)
        self.recent_429s.append(1 if status_code == 429 else 0)

    def calculate_percentiles(self) -> Dict[str, float]:
        if not self.recent_latencies:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0}
        sorted_lats = sorted(list(self.recent_latencies))
        n = len(sorted_lats)
        return {
            "p50": round(sorted_lats[int(n * 0.50)], 2),
            "p95": round(sorted_lats[min(n - 1, int(n * 0.95))], 2),
            "p99": round(sorted_lats[min(n - 1, int(n * 0.99))], 2)
        }

    def get_throughput(self) -> float:
        now = time.time()
        recent = [t for t in self.processed_timestamps if now - t <= 5.0]
        if not recent:
            return 0.0
        return round(len(recent) / 5.0, 1)

    def get_error_rate(self) -> float:
        if not self.recent_errors:
            return 0.0
        return round(sum(self.recent_errors) / len(self.recent_errors), 3)

    def get_429_rate(self) -> float:
        if not self.recent_429s:
            return 0.0
        return round(sum(self.recent_429s) / len(self.recent_429s), 3)

    async def get_system_metrics(self) -> Dict[str, Any]:
        async with AsyncSessionLocal() as session:
            # Query counts
            total_events = (await session.execute(select(func.count(Event.id)))).scalar() or 0
            success_count = (await session.execute(select(func.count(Event.id)).where(Event.status == EventStatus.SUCCESS.value))).scalar() or 0
            failed_count = (await session.execute(select(func.count(Event.id)).where(Event.status == EventStatus.FAILED.value))).scalar() or 0
            retrying_count = (await session.execute(select(func.count(Event.id)).where(Event.status == EventStatus.RETRYING.value))).scalar() or 0
            dlq_count = (await session.execute(select(func.count(DeadLetterEvent.id)))).scalar() or 0
            duplicate_count = (await session.execute(select(func.count(Event.id)).where(Event.is_duplicate == True))).scalar() or 0
            
            # Query priority counts
            p_crit = (await session.execute(select(func.count(Event.id)).where(Event.priority == "CRITICAL", Event.status.in_(["QUEUED", "PROCESSING", "RETRYING"])))).scalar() or 0
            p_high = (await session.execute(select(func.count(Event.id)).where(Event.priority == "HIGH", Event.status.in_(["QUEUED", "PROCESSING", "RETRYING"])))).scalar() or 0
            p_norm = (await session.execute(select(func.count(Event.id)).where(Event.priority == "NORMAL", Event.status.in_(["QUEUED", "PROCESSING", "RETRYING"])))).scalar() or 0
            p_low = (await session.execute(select(func.count(Event.id)).where(Event.priority == "LOW", Event.status.in_(["QUEUED", "PROCESSING", "RETRYING"])))).scalar() or 0

            # Query workers
            workers_res = await session.execute(select(Worker))
            workers = workers_res.scalars().all()
            total_workers = len(workers)
            active_workers = len([w for w in workers if w.status in [WorkerStatus.HEALTHY.value, WorkerStatus.BUSY.value]])

        queue_stats = await stream_manager.get_queue_stats()
        percentiles = self.calculate_percentiles()
        throughput = self.get_throughput()
        error_rate = self.get_error_rate()
        http_429_rate = self.get_429_rate()
        
        success_rate = round((success_count / total_events * 100.0) if total_events > 0 else 100.0, 1)

        cb = get_circuit_breaker()
        policy_engine = get_policy_engine()

        # Update Policy Engine telemetry
        priority_dist = {"CRITICAL": p_crit, "HIGH": p_high, "NORMAL": p_norm, "LOW": p_low}
        policy_engine.state_manager.update_metrics(
            queue_depth=queue_stats.get("queue_depth", 0),
            ingestion_rate=throughput,
            processing_rate=throughput,
            worker_utilization=round(active_workers / max(1, total_workers), 2),
            p50=percentiles["p50"],
            p95=percentiles["p95"],
            p99=percentiles["p99"],
            error_rate=error_rate,
            retry_rate=error_rate,
            http_429_rate=http_429_rate,
            active_workers=active_workers,
            priority_counts=priority_dist,
            circuit_state=cb.state
        )

        return {
            "total_events": total_events,
            "events_per_second": throughput,
            "success_count": success_count,
            "failed_count": failed_count,
            "retrying_count": retrying_count,
            "dlq_count": dlq_count,
            "duplicate_count": duplicate_count,
            "success_rate": success_rate,
            "queue_depth": queue_stats.get("queue_depth", 0),
            "pending_events": queue_stats.get("pending_count", 0),
            "active_workers": active_workers,
            "total_workers": total_workers,
            "p50_latency_ms": percentiles["p50"],
            "p95_latency_ms": percentiles["p95"],
            "p99_latency_ms": percentiles["p99"],
            "error_rate": error_rate,
            "http_429_rate": http_429_rate,
            "current_mode": policy_engine.current_mode,
            "circuit_breaker_state": cb.state,
            "delayed_count": policy_engine.backpressure.delayed_count,
            "throttled_count": policy_engine.backpressure.throttled_count,
            "batched_count": policy_engine.backpressure.batched_count,
            "priority_distribution": priority_dist,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def _metrics_broadcast_loop(self):
        while self.is_running:
            try:
                metrics = await self.get_system_metrics()
                await ws_manager.broadcast("METRICS_UPDATE", metrics)
            except Exception as e:
                logger.error(f"Error in metrics broadcast loop: {e}")
            await asyncio.sleep(1.0)

    def start(self):
        if not self.is_running:
            self.is_running = True
            self._task = asyncio.create_task(self._metrics_broadcast_loop())
            logger.info("Metrics collector broadcast loop started.")

    def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()

metrics_collector = MetricsCollector()

