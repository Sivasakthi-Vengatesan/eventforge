import asyncio
import uuid
import pytest
import httpx
from backend.app.main import app
from backend.app.security.hmac import generate_stripe_signature
from backend.app.database.connection import AsyncSessionLocal
from backend.app.models.event import Event
from sqlalchemy import select

@pytest.mark.asyncio
async def test_concurrent_idempotency_burst():
    """
    Sends 20 simultaneous duplicate webhook requests for the exact same event ID.
    Asserts atomic insertion prevents duplicate processing: exactly 1 accepted, 19 flagged duplicate.
    """
    evt_id = f"evt_concurrent_{uuid.uuid4().hex[:10]}"
    payload = f'{{"id":"{evt_id}","type":"payment_intent.succeeded","amount":10000}}'.encode("utf-8")
    secret = "whsec_stripe_test_secret_38472948"
    sig = generate_stripe_signature(payload, secret)
    headers = {"Stripe-Signature": sig, "Content-Type": "application/json"}

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Launch 20 concurrent requests
        tasks = [
            client.post("/api/v1/webhooks/stripe", content=payload, headers=headers)
            for _ in range(20)
        ]
        responses = await asyncio.gather(*tasks)

    statuses = [r.status_code for r in responses]
    assert all(s == 202 for s in statuses)

    body_statuses = [r.json()["status"] for r in responses]
    accepted_count = body_statuses.count("ACCEPTED")
    duplicate_count = body_statuses.count("DUPLICATE")

    assert accepted_count == 1, f"Expected exactly 1 ACCEPTED, got {accepted_count}"
    assert duplicate_count == 19, f"Expected exactly 19 DUPLICATE, got {duplicate_count}"

    # Verify Database state
    async with AsyncSessionLocal() as session:
        stmt = select(Event).where(Event.provider == "stripe", Event.event_id == evt_id)
        res = await session.execute(stmt)
        event = res.scalar_one_or_none()
        assert event is not None
        assert event.is_duplicate is True
        assert event.duplicate_count == 19
