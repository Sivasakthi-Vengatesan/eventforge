import uuid
import pytest
import httpx
from backend.app.main import app
from backend.app.database.connection import init_db
from backend.app.security.hmac import generate_stripe_signature, generate_razorpay_signature

@pytest.mark.asyncio
async def test_health_endpoints():
    await init_db()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "database" in data
        assert "redis" in data

@pytest.mark.asyncio
async def test_stripe_webhook_ingest_success():
    await init_db()
    evt_id = f"evt_stripe_test_{uuid.uuid4().hex[:8]}"
    payload = f'{{"id":"{evt_id}","type":"payment_intent.succeeded","data":{{"amount":5000}}}}'.encode("utf-8")
    secret = "whsec_stripe_test_secret_38472948"
    sig = generate_stripe_signature(payload, secret)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/webhooks/stripe",
            content=payload,
            headers={"Stripe-Signature": sig, "Content-Type": "application/json"}
        )
        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "ACCEPTED"
        assert data["event_id"] == evt_id
        assert data["provider"] == "stripe"

@pytest.mark.asyncio
async def test_idempotency_duplicate_rejection():
    await init_db()
    evt_id = f"evt_dup_test_{uuid.uuid4().hex[:8]}"
    payload = f'{{"id":"{evt_id}","type":"charge.captured"}}'.encode("utf-8")
    secret = "whsec_stripe_test_secret_38472948"
    sig = generate_stripe_signature(payload, secret)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # First call -> ACCEPTED
        resp1 = await client.post(
            "/api/v1/webhooks/stripe",
            content=payload,
            headers={"Stripe-Signature": sig, "Content-Type": "application/json"}
        )
        assert resp1.status_code == 202
        assert resp1.json()["status"] == "ACCEPTED"

        # Second identical call -> DUPLICATE
        resp2 = await client.post(
            "/api/v1/webhooks/stripe",
            content=payload,
            headers={"Stripe-Signature": sig, "Content-Type": "application/json"}
        )
        assert resp2.status_code == 202
        assert resp2.json()["status"] == "DUPLICATE"
        assert "Duplicate webhook ignored" in resp2.json()["message"]

@pytest.mark.asyncio
async def test_events_list_and_metrics():
    await init_db()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        events_resp = await client.get("/api/v1/events")
        assert events_resp.status_code == 200
        events_data = events_resp.json()
        assert "items" in events_data
        assert "total" in events_data

        metrics_resp = await client.get("/api/v1/metrics")
        assert metrics_resp.status_code == 200
        metrics_data = metrics_resp.json()
        assert "total_events" in metrics_data
        assert "success_rate" in metrics_data
