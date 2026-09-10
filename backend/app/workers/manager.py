import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional
from sqlalchemy import select
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.database.connection import AsyncSessionLocal
from backend.app.models.event import Event, EventStatus
from backend.app.queue.stream_manager import stream_manager
from backend.app.workers.worker import AsyncEventWorker

class WorkerManager:
    def __init__(self, default_count: int = settings.WORKER_COUNT, min_count: int = 2, max_count: int = 8):
        self.default_count = default_count
        self.min_count = min_count
        self.max_count = max_count
        self.workers: Dict[str, AsyncEventWorker] = {}
        self._retry_scheduler_task: Optional[asyncio.Task] = None
        self._is_running = False

    def start_pool(self, count: int = None):
        target_count = count or self.default_count
        self._is_running = True
        logger.info(f"Starting Worker Pool with {target_count} workers...")
        for i in range(1, target_count + 1):
            worker_id = f"worker-{i}"
            if worker_id not in self.workers:
                worker = AsyncEventWorker(worker_id)
                self.workers[worker_id] = worker
                worker.start()
        
        # Start durable retry recovery scheduler
        if self._retry_scheduler_task is None or self._retry_scheduler_task.done():
            self._retry_scheduler_task = asyncio.create_task(self._durable_retry_recovery_loop())
            
        logger.info("Worker Pool and Durable Retry Scheduler initialized successfully.")

    async def _durable_retry_recovery_loop(self):
        """
        Durable Retry Scheduler: Scans PostgreSQL for due retry events that were scheduled,
        ensuring crashes and process restarts never lose a scheduled retry.
        """
        while self._is_running:
            try:
                now = datetime.now(timezone.utc)
                async with AsyncSessionLocal() as session:
                    stmt = (
                        select(Event)
                        .where(
                            Event.status == EventStatus.RETRYING.value,
                            Event.next_retry_at <= now
                        )
                        .limit(20)
                    )
                    res = await session.execute(stmt)
                    due_events = res.scalars().all()
                    
                    for event in due_events:
                        event.status = EventStatus.QUEUED.value
                        event.queued_at = now
                        event.next_retry_at = None
                        await session.commit()
                        
                        await stream_manager.push_event(
                            event_id=event.event_id,
                            provider=event.provider,
                            event_type=event.event_type,
                            payload=event.payload,
                            retry_count=event.retry_count
                        )
                        logger.info(
                            f"Durable Retry Scheduler dispatched due retry for {event.provider}:{event.event_id} (Attempt {event.retry_count})"
                        )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in durable retry recovery loop: {e}", exc_info=False)
            
            await asyncio.sleep(1.0)

    async def set_target_concurrency(self, target_count: int):
        """Dynamically scales worker concurrency up or down."""
        target_count = max(self.min_count, min(self.max_count, target_count))
        current_count = len(self.workers)
        
        if target_count > current_count:
            # Scale UP
            for i in range(current_count + 1, target_count + 1):
                worker_id = f"worker-{i}"
                if worker_id not in self.workers:
                    w = AsyncEventWorker(worker_id)
                    self.workers[worker_id] = w
                    w.start()
            logger.info(f"Worker Pool scaled UP: {current_count} -> {target_count} workers")
        elif target_count < current_count:
            # Scale DOWN
            for i in range(current_count, target_count, -1):
                worker_id = f"worker-{i}"
                if worker_id in self.workers:
                    await self.workers[worker_id].stop()
                    del self.workers[worker_id]
            logger.info(f"Worker Pool scaled DOWN: {current_count} -> {target_count} workers")

    async def stop_pool(self):
        logger.info("Stopping Worker Pool...")
        self._is_running = False
        if self._retry_scheduler_task:
            self._retry_scheduler_task.cancel()
            try:
                await self._retry_scheduler_task
            except asyncio.CancelledError:
                pass
            self._retry_scheduler_task = None
            
        for worker_id, worker in list(self.workers.items()):
            await worker.stop()
        self.workers.clear()
        logger.info("All workers in pool stopped.")

    async def restart_worker(self, worker_id: str):
        if worker_id in self.workers:
            await self.workers[worker_id].stop()
            w = AsyncEventWorker(worker_id)
            self.workers[worker_id] = w
            w.start()
            logger.info(f"Worker {worker_id} restarted.")

    async def kill_worker(self, worker_id: str):
        """Simulates worker crash."""
        if worker_id in self.workers:
            await self.workers[worker_id].stop()
            logger.warning(f"Simulated crash for {worker_id}!")

    def get_active_worker_ids(self) -> List[str]:
        return list(self.workers.keys())

worker_manager = WorkerManager()


