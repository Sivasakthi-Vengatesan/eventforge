import asyncio
import time
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.database.connection import AsyncSessionLocal
from backend.app.models.event import Event, EventStatus
from backend.app.models.worker import Worker, WorkerStatus
from backend.app.queue.stream_manager import stream_manager
from backend.app.services.retry import retry_service
from backend.app.services.dlq_service import dlq_service
from backend.app.workers.processor import event_processor
from backend.app.adaptive.policy_engine import get_policy_engine
from backend.app.monitoring.websocket_manager import ws_manager
from backend.app.monitoring.metrics_collector import metrics_collector

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class AsyncEventWorker:
    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.status = WorkerStatus.STARTING
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.processed_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.total_duration_ms = 0.0

    async def _update_db_worker_state(
        self,
        db: AsyncSession,
        status: WorkerStatus,
        event_id: Optional[str] = None,
        provider: Optional[str] = None,
        event_type: Optional[str] = None
    ):
        self.status = status
        stmt = select(Worker).where(Worker.id == self.worker_id)
        res = await db.execute(stmt)
        w = res.scalar_one_or_none()
        
        if not w:
            w = Worker(
                id=self.worker_id,
                status=status.value,
                started_at=utc_now(),
                last_heartbeat=utc_now()
            )
            db.add(w)
        else:
            w.status = status.value
            w.current_event_id = event_id
            w.current_event_provider = provider
            w.current_event_type = event_type
            w.processed_count = self.processed_count
            w.success_count = self.success_count
            w.failure_count = self.failure_count
            w.total_processing_time_ms = self.total_duration_ms
            w.average_duration_ms = round(self.total_duration_ms / max(1, self.processed_count), 2)
            w.last_heartbeat = utc_now()
            
        await db.commit()
        await ws_manager.broadcast("WORKER_UPDATED", {
            "id": self.worker_id,
            "status": status.value,
            "current_event_id": event_id,
            "processed_count": self.processed_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "last_heartbeat": utc_now().isoformat()
        })

    async def _process_single_message(self, stream_msg_id: str, msg_data: dict):
        event_id = msg_data.get("event_id")
        provider = msg_data.get("provider")
        event_type = msg_data.get("event_type")
        retry_count = int(msg_data.get("retry_count", 0))

        start_ts = time.time()

        async with AsyncSessionLocal() as session:
            # Fetch event from database
            stmt = select(Event).where(Event.provider == provider, Event.event_id == event_id)
            res = await session.execute(stmt)
            event = res.scalar_one_or_none()

            if not event:
                logger.warning(f"Event {provider}:{event_id} not found in database. ACKing message.")
                await stream_manager.ack_event(stream_msg_id)
                return

            # Mark state as PROCESSING
            event.status = EventStatus.PROCESSING.value
            event.started_at = utc_now()
            event.retry_count = retry_count
            await session.commit()
            
            await self._update_db_worker_state(session, WorkerStatus.BUSY, event_id, provider, event_type)
            await ws_manager.broadcast("EVENT_STATUS_CHANGED", {
                "event_id": event_id,
                "provider": provider,
                "event_type": event_type,
                "status": "PROCESSING",
                "worker_id": self.worker_id,
                "retry_count": retry_count
            })

            # Apply Adaptive Backpressure if necessary
            policy_engine = get_policy_engine()
            should_delay, delay_sec = policy_engine.backpressure.should_delay(event.priority, policy_engine.current_mode)
            if should_delay and delay_sec > 0:
                logger.info(f"Applying adaptive backpressure: delaying {event.priority} event {event_id} by {delay_sec}s in {policy_engine.current_mode} mode")
                await asyncio.sleep(delay_sec)

            # Execute event verification
            is_success, error_msg, status_code, is_retryable = await event_processor.process_event(
                session, event, self.worker_id
            )

            duration_ms = round((time.time() - start_ts) * 1000, 2)
            self.processed_count += 1
            self.total_duration_ms += duration_ms
            metrics_collector.record_event_completion(duration_ms)

            if is_success:
                self.success_count += 1
                event.status = EventStatus.SUCCESS.value
                event.completed_at = utc_now()
                event.processing_duration_ms = duration_ms
                event.error_message = None
                await session.commit()
                
                # Acknowledge stream message
                await stream_manager.ack_event(stream_msg_id)
                logger.info(f"Event {provider}:{event_id} processed successfully by {self.worker_id} ({duration_ms}ms)")
                
                await ws_manager.broadcast("EVENT_STATUS_CHANGED", {
                    "event_id": event_id,
                    "provider": provider,
                    "event_type": event_type,
                    "status": "SUCCESS",
                    "duration_ms": duration_ms,
                    "worker_id": self.worker_id
                })
            else:
                self.failure_count += 1
                # Check retry policy
                if is_retryable and retry_count < event.max_retries:
                    new_retry_count = retry_count + 1
                    event.status = EventStatus.RETRYING.value
                    event.retry_count = new_retry_count
                    event.error_message = error_msg
                    await session.commit()

                    base_delay = retry_service.calculate_backoff_delay(new_retry_count)
                    # Apply adaptive retry multiplier
                    delay = base_delay * policy_engine.controller.current_retry_multiplier
                    logger.warning(f"Event {event_id} failed. Scheduling adaptive retry {new_retry_count}/{event.max_retries} in {delay:.2f}s (Multiplier: {policy_engine.controller.current_retry_multiplier}x): {error_msg}")
                    
                    # ACK current stream message and schedule re-enqueue after delay
                    await stream_manager.ack_event(stream_msg_id)
                    
                    async def delayed_requeue(delay_sec: float, evt_id: str, prov: str, evt_type: str, pl: dict, retries: int):
                        await asyncio.sleep(delay_sec)
                        await stream_manager.push_event(evt_id, prov, evt_type, pl, retry_count=retries)

                    asyncio.create_task(delayed_requeue(delay, event_id, provider, event_type, event.payload, new_retry_count))

                    await ws_manager.broadcast("EVENT_STATUS_CHANGED", {
                        "event_id": event_id,
                        "provider": provider,
                        "event_type": event_type,
                        "status": "RETRYING",
                        "retry_count": new_retry_count,
                        "next_retry_delay_sec": round(delay, 2),
                        "error": error_msg
                    })
                else:
                    # Move to DLQ
                    reason = f"Exceeded MAX_RETRIES ({event.max_retries}): {error_msg}" if is_retryable else f"Fatal Non-Retryable Error: {error_msg}"
                    await dlq_service.send_to_dlq(session, event, failure_reason=reason)
                    await stream_manager.ack_event(stream_msg_id)
                    
                    await ws_manager.broadcast("EVENT_STATUS_CHANGED", {
                        "event_id": event_id,
                        "provider": provider,
                        "event_type": event_type,
                        "status": "DLQ",
                        "retry_count": retry_count,
                        "error": reason
                    })

            await self._update_db_worker_state(session, WorkerStatus.HEALTHY, None, None, None)

    async def _run_loop(self):
        logger.info(f"Worker {self.worker_id} started consumption loop.")
        async with AsyncSessionLocal() as session:
            await self._update_db_worker_state(session, WorkerStatus.HEALTHY)

        claim_counter = 0
        while self.is_running:
            try:
                # 1. Read batch from stream
                messages = await stream_manager.read_events(consumer_name=self.worker_id, count=1, block_ms=500)
                
                if messages:
                    for msg_id, msg_data in messages:
                        if not self.is_running:
                            break
                        await self._process_single_message(msg_id, msg_data)
                else:
                    # Heartbeat update every ~10 idle cycles
                    claim_counter += 1
                    if claim_counter % 10 == 0:
                        async with AsyncSessionLocal() as session:
                            await self._update_db_worker_state(session, WorkerStatus.HEALTHY)
                            
                    # Rescue stuck messages periodically
                    if claim_counter >= 30:
                        claim_counter = 0
                        stuck = await stream_manager.claim_stuck_events(consumer_name=self.worker_id, min_idle_ms=15000, count=2)
                        for msg_id, msg_data in stuck:
                            logger.info(f"Worker {self.worker_id} claimed pending orphaned event {msg_data.get('event_id')}")
                            await self._process_single_message(msg_id, msg_data)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {self.worker_id} encountered loop error: {e}", exc_info=True)
                await asyncio.sleep(1.0)

        async with AsyncSessionLocal() as session:
            await self._update_db_worker_state(session, WorkerStatus.STOPPED)
        logger.info(f"Worker {self.worker_id} loop terminated gracefully.")

    def start(self):
        if not self.is_running:
            self.is_running = True
            self._task = asyncio.create_task(self._run_loop())

    async def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
