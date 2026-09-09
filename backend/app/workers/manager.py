import asyncio
from typing import Dict, List
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.workers.worker import AsyncEventWorker

class WorkerManager:
    def __init__(self, default_count: int = settings.WORKER_COUNT, min_count: int = 2, max_count: int = 8):
        self.default_count = default_count
        self.min_count = min_count
        self.max_count = max_count
        self.workers: Dict[str, AsyncEventWorker] = {}

    def start_pool(self, count: int = None):
        target_count = count or self.default_count
        logger.info(f"Starting Worker Pool with {target_count} workers...")
        for i in range(1, target_count + 1):
            worker_id = f"worker-{i}"
            if worker_id not in self.workers:
                worker = AsyncEventWorker(worker_id)
                self.workers[worker_id] = worker
                worker.start()
        logger.info("Worker Pool initialized successfully.")

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

