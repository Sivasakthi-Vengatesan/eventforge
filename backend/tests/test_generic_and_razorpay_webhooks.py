import uuid
import pytest
import httpx
from backend.app.main import app
from backend.app.core.config import settings
from backend.app.security.hmac import generate_razorpay_signature, generate_generic_signature

@pytest.mark.asyncio
async def test_razorpay_webhook_ingest_and_rejection():
    """Verifies Razorpay webhook HMAC verification, acceptance, and signature tampering rejection."""
    evt_id = f"rzp_evt_{uuid.uuid4().hex[:8]}"
    payload = f'{{"event_id":"{evt_id}","event":"payment.captured","amount":25000}}'.encode("utf-8")
    secret = settings.WEBHOOK_SECRET_RAZORPAY
    sig = generate_razorpay_signature(payload, secret)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Valid Signature -> 202 ACCEPTED
        resp = await client.post(
            "/api/v1/webhooks/razorpay",
            content=payload,
            headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"}
        )
        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "ACCEPTED"
        assert data["provider"] == "razorpay"

        # 2. Tampered Signature -> 403 FORBIDDEN
        bad_resp = await client.post(
            "/api/v1/webhooks/razorpay",
            content=payload,
            headers={"X-Razorpay-Signature": "invalid_sig_abc", "Content-Type": "application/json"}
        )
        assert bad_resp.status_code == 403

@pytest.mark.asyncio
async def test_generic_webhook_pipeline():
    """Verifies Generic webhook routes through the unified pipeline with HMAC security."""
    evt_id = f"gen_evt_{uuid.uuid4().hex[:8]}"
    payload = f'{{"event_id":"{evt_id}","event_type":"user.signup","email":"test@example.com"}}'.encode("utf-8")
    secret = settings.WEBHOOK_SECRET_GENERIC
    sig = generate_generic_signature(payload, secret)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Ingest valid generic webhook
        resp = await client.post(
            "/api/v1/webhooks/generic",
            content=payload,
            headers={"X-Signature-256": sig, "Content-Type": "application/json"}
        )
        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "ACCEPTED"
        assert data["provider"] == "generic"

        # 2. Duplicate detection
        dup_resp = await client.post(
            "/api/v1/webhooks/generic",
            content=payload,
            headers={"X-Signature-256": sig, "Content-Type": "application/json"}
        )
        assert dup_resp.status_code == 202
        assert dup_resp.json()["status"] == "DUPLICATE"
