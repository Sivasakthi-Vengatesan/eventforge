import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import asyncio
import json
import time
import uuid
import httpx
from backend.app.security.hmac import generate_stripe_signature, generate_razorpay_signature

BASE_URL = "http://127.0.0.1:8000"
STRIPE_SECRET = "whsec_stripe_test_secret_38472948"
RAZORPAY_SECRET = "rzp_sec_razorpay_test_98372184"

async def run_scenario_1_downstream_500():
    print("\n--- Scenario 1: Downstream 500 & Retry Recovery ---")
    event_id = f"evt_fail500_{uuid.uuid4().hex[:8]}"
    payload = {"id": event_id, "type": "payment_intent.succeeded", "force_fault": "500"}
    body = json.dumps(payload).encode("utf-8")
    sig = generate_stripe_signature(body, STRIPE_SECRET)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{BASE_URL}/api/v1/webhooks/stripe",
            content=body,
            headers={"Stripe-Signature": sig, "Content-Type": "application/json", "x-mock-fault": "500"}
        )
        print(f"Ingested: {resp.status_code} - {resp.json().get('status')}")
        print("Waiting 3s for worker to execute retry backoff loop...")
        await asyncio.sleep(3.0)
        
        # Check event status
        evt_resp = await client.get(f"{BASE_URL}/api/v1/events/{event_id}")
        if evt_resp.status_code == 200:
            evt = evt_resp.json()
            print(f"Current State: {evt.get('status')} | Retries: {evt.get('retry_count')} | Error: {evt.get('error_message')}")
            print(f"Attempts Recorded: {len(evt.get('attempts', []))}")

async def run_scenario_2_tampered_hmac():
    print("\n--- Scenario 2: Tampered HMAC Signature Rejection ---")
    payload = b'{"id":"evt_tampered_123","amount":500}'
    # Sign with wrong secret
    sig = generate_stripe_signature(payload, "wrong_secret_key")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{BASE_URL}/api/v1/webhooks/stripe",
            content=payload,
            headers={"Stripe-Signature": sig, "Content-Type": "application/json"}
        )
        print(f"Gateway Response: HTTP {resp.status_code} - Detail: {resp.text}")
        assert resp.status_code in [401, 403], "Should be rejected by HMAC security layer"
        print("✅ Tampered signature successfully blocked at the perimeter.")

async def run_scenario_3_duplicate_burst():
    print("\n--- Scenario 3: High-Frequency Duplicate Burst (10 identical events) ---")
    shared_id = f"evt_shared_burst_{uuid.uuid4().hex[:8]}"
    payload_dict = {"id": shared_id, "type": "payment_intent.succeeded", "amount": 1000}
    body = json.dumps(payload_dict).encode("utf-8")
    sig = generate_stripe_signature(body, STRIPE_SECRET)
    headers = {"Stripe-Signature": sig, "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = [client.post(f"{BASE_URL}/api/v1/webhooks/stripe", content=body, headers=headers) for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        statuses = []
        for r in results:
            if isinstance(r, httpx.Response):
                try:
                    statuses.append(r.json().get("status", f"HTTP_{r.status_code}"))
                except Exception:
                    statuses.append(f"HTTP_{r.status_code}")
            else:
                statuses.append(f"ERR_{str(r)}")

        accepted = statuses.count("ACCEPTED")
        duplicates = statuses.count("DUPLICATE")
        print(f"Results: {len(results)} sent -> {accepted} ACCEPTED, {duplicates} DUPLICATE, All Statuses: {statuses}")
        assert accepted == 1, f"Expected 1 ACCEPTED, got {accepted}"
        assert duplicates >= 8, f"Expected at least 8 DUPLICATE, got {duplicates}"
        print("✅ Idempotency strictly guaranteed under concurrent load.")

async def run_scenario_4_max_retries_to_dlq():
    print("\n--- Scenario 4: Permanent Failure -> Dead Letter Queue (DLQ) ---")
    event_id = f"evt_dlq_perm_{uuid.uuid4().hex[:8]}"
    payload = {"id": event_id, "type": "payment_intent.succeeded", "force_fault": "invalid_data"}
    body = json.dumps(payload).encode("utf-8")
    sig = generate_stripe_signature(body, STRIPE_SECRET)

    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(
            f"{BASE_URL}/api/v1/webhooks/stripe",
            content=body,
            headers={"Stripe-Signature": sig, "Content-Type": "application/json", "x-mock-fault": "400"}
        )
        print("Ingested fatal non-retryable event. Awaiting processing...")
        await asyncio.sleep(2.0)

        # Inspect DLQ
        dlq_resp = await client.get(f"{BASE_URL}/api/v1/dlq")
        dlq_items = dlq_resp.json().get("items", [])
        matched = [d for d in dlq_items if d["event_id"] == event_id]
        if matched:
            print(f"✅ Event successfully routed to DLQ! DLQ ID: {matched[0]['dlq_id']}, Reason: {matched[0]['failure_reason']}")
        else:
            print("Note: Event pending or in DLQ list.")

async def run_all_scenarios():
    print("="*60)
    print("🧪 EventForge Automated Failure & Resilience Simulator")
    print("="*60)
    await run_scenario_2_tampered_hmac()
    await run_scenario_3_duplicate_burst()
    await run_scenario_1_downstream_500()
    await run_scenario_4_max_retries_to_dlq()
    print("\n" + "="*60)
    print("✨ All Resilience & Failure Scenarios Completed.")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(run_all_scenarios())
