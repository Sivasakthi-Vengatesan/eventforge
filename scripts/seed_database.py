import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import asyncio
import json
import random
import time
import uuid
from backend.app.database.connection import init_db, AsyncSessionLocal
from backend.app.models.event import Event, EventStatus, EventAttempt, IdempotencyRecord
from backend.app.models.dlq import DeadLetterEvent
from backend.app.models.worker import Worker, WorkerStatus

async def seed_data():
    print("🌱 Seeding EventForge database with initial realistic history...")
    await init_db()
    async with AsyncSessionLocal() as session:
        # Seed workers (upsert)
        from sqlalchemy import select
        for i in range(1, 5):
            wid = f"worker-{i}"
            res = await session.execute(select(Worker).where(Worker.id == wid))
            w = res.scalar_one_or_none()
            if not w:
                w = Worker(
                    id=wid,
                    status=WorkerStatus.HEALTHY.value,
                    processed_count=random.randint(120, 450),
                    success_count=random.randint(110, 430),
                    failure_count=random.randint(2, 15),
                    total_processing_time_ms=random.uniform(5000, 18000),
                    average_duration_ms=round(random.uniform(35.0, 65.0), 2)
                )
                session.add(w)
            else:
                w.processed_count = max(w.processed_count, random.randint(120, 450))
                w.success_count = max(w.success_count, random.randint(110, 430))
                w.average_duration_ms = round(random.uniform(35.0, 65.0), 2)

        # Seed sample events across statuses
        providers = ["stripe", "razorpay", "github", "generic"]
        event_types = {
            "stripe": ["payment_intent.succeeded", "charge.refunded", "customer.subscription.created"],
            "razorpay": ["payment.captured", "payment.failed", "refund.created"],
            "github": ["push", "pull_request", "deployment"],
            "generic": ["order.created", "inventory.low"]
        }

        for i in range(30):
            prov = random.choice(providers)
            etype = random.choice(event_types[prov])
            eid = f"evt_{prov[:3]}_seed_{uuid.uuid4().hex[:8]}"
            status = random.choice([EventStatus.SUCCESS.value, EventStatus.SUCCESS.value, EventStatus.RETRYING.value, EventStatus.FAILED.value])
            
            dur = round(random.uniform(25.0, 95.0), 2)
            evt = Event(
                event_id=eid,
                provider=prov,
                event_type=etype,
                payload={"amount": random.randint(1000, 50000), "currency": "usd", "customer": f"cus_{i}"},
                status=status,
                retry_count=1 if status == EventStatus.RETRYING.value else (5 if status == EventStatus.FAILED.value else 0),
                processing_duration_ms=dur,
                is_duplicate=False
            )
            session.add(evt)

            # Add idempotency record
            rec = IdempotencyRecord(
                key=f"{prov}:{eid}",
                provider=prov,
                event_id=eid,
                hits=1,
                status="PROCESSED"
            )
            session.add(rec)

        # Seed a sample DLQ event
        dlq_evt = DeadLetterEvent(
            dlq_id=f"dlq_seed_{uuid.uuid4().hex[:8]}",
            event_id="evt_str_dlq_sample_01",
            provider="stripe",
            event_type="payment_intent.payment_failed",
            payload={"amount": 99000, "currency": "usd", "error": "card_velocity_exceeded"},
            failure_reason="Downstream HTTP 500: Database deadlock after 5 retries",
            retry_count=5,
            is_resolved=False
        )
        session.add(dlq_evt)

        await session.commit()
    print("✅ Database seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed_data())
