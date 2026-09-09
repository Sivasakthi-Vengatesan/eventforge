import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import argparse
import asyncio
import json
import random
import time
import uuid
import httpx
from backend.app.security.hmac import (
    generate_stripe_signature,
    generate_razorpay_signature,
    generate_github_signature,
    generate_generic_signature
)

STRIPE_SECRET = "whsec_stripe_test_secret_38472948"
RAZORPAY_SECRET = "rzp_sec_razorpay_test_98372184"
GITHUB_SECRET = "gh_sec_github_test_84729184"
GENERIC_SECRET = "gen_sec_generic_test_19284729"

EVENT_TEMPLATES = {
    "stripe": [
        ("payment_intent.succeeded", {"amount": 5000, "currency": "usd", "status": "succeeded"}),
        ("payment_intent.payment_failed", {"amount": 2500, "currency": "usd", "last_payment_error": "card_declined"}),
        ("charge.refunded", {"amount_refunded": 1200, "currency": "usd"}),
        ("customer.subscription.created", {"plan": "pro_tier_monthly", "status": "active"}),
    ],
    "razorpay": [
        ("payment.captured", {"amount": 499900, "currency": "INR", "method": "upi"}),
        ("payment.failed", {"amount": 99900, "currency": "INR", "error_code": "BAD_REQUEST_ERROR"}),
        ("refund.created", {"amount": 200000, "currency": "INR", "speed": "optimum"}),
        ("order.paid", {"amount": 750000, "currency": "INR", "status": "paid"}),
    ],
    "github": [
        ("push", {"ref": "refs/heads/main", "commits_count": 2, "pusher": "dev_engineer"}),
        ("pull_request", {"action": "opened", "number": 42, "title": "feat: async worker queue"}),
        ("issues", {"action": "opened", "number": 105, "title": "fix: connection pool overflow"}),
        ("deployment", {"environment": "production", "status": "initiated"}),
    ],
    "generic": [
        ("order.created", {"order_id": "ord_8829", "items_count": 3, "total": 149.50}),
        ("user.signup", {"tier": "free", "referral": "hacker_news"}),
        ("inventory.low", {"sku": "SKU-992", "remaining": 4}),
    ]
}

async def send_single_event(
    client: httpx.AsyncClient,
    base_url: str,
    provider: str,
    event_id: str,
    event_type: str,
    data: dict,
    is_invalid_signature: bool = False,
    force_fault: str = None
) -> dict:
    prov = provider.lower()
    payload_dict = {"id": event_id, "type": event_type, "data": data, "timestamp": int(time.time())}
    if force_fault:
        payload_dict["force_fault"] = force_fault
        
    payload_bytes = json.dumps(payload_dict).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    
    if force_fault:
        headers["x-mock-fault"] = force_fault

    secret = (
        STRIPE_SECRET if prov == "stripe"
        else RAZORPAY_SECRET if prov == "razorpay"
        else GITHUB_SECRET if prov == "github"
        else GENERIC_SECRET
    )

    if is_invalid_signature:
        secret = "invalid_tampered_secret_key"

    if prov == "stripe":
        headers["Stripe-Signature"] = generate_stripe_signature(payload_bytes, secret)
    elif prov == "razorpay":
        headers["X-Razorpay-Signature"] = generate_razorpay_signature(payload_bytes, secret)
    elif prov == "github":
        headers["X-Hub-Signature-256"] = generate_github_signature(payload_bytes, secret)
        headers["X-GitHub-Event"] = event_type
        headers["X-GitHub-Delivery"] = event_id
    else:
        headers["X-Signature-256"] = generate_generic_signature(payload_bytes, secret)

    start = time.time()
    try:
        resp = await client.post(f"{base_url}/api/v1/webhooks/{prov}", content=payload_bytes, headers=headers)
        latency_ms = (time.time() - start) * 1000
        return {
            "status_code": resp.status_code,
            "response": resp.json() if resp.status_code < 500 else resp.text,
            "latency_ms": latency_ms,
            "is_duplicate": resp.json().get("status") == "DUPLICATE" if resp.status_code == 202 else False,
            "is_rejected": resp.status_code in [401, 403],
            "is_accepted": resp.status_code == 202 and resp.json().get("status") == "ACCEPTED"
        }
    except Exception as e:
        return {"status_code": 0, "error": str(e), "latency_ms": (time.time() - start) * 1000}

async def generate_events(
    count: int = 100,
    provider: str = "random",
    concurrency: int = 10,
    duplicate_rate: float = 0.05,
    failure_rate: float = 0.05,
    invalid_signature_rate: float = 0.02,
    base_url: str = "http://127.0.0.1:8000"
):
    print(f"\n🚀 EventForge Synthetic Generator: Generating {count} events...")
    print(f"   Provider: {provider} | Concurrency: {concurrency} | Duplicate Rate: {duplicate_rate * 100:.1f}% | Target: {base_url}")

    providers = ["stripe", "razorpay", "github", "generic"] if provider == "random" else [provider]
    
    # Pre-generate duplicate pools
    duplicate_pool = [f"evt_dup_{uuid.uuid4().hex[:10]}" for _ in range(max(1, int(count * duplicate_rate)))]
    
    semaphore = asyncio.Semaphore(concurrency)
    stats = {"accepted": 0, "duplicates": 0, "rejected": 0, "errors": 0, "latencies": []}

    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = []
        for i in range(count):
            prov = random.choice(providers)
            template = random.choice(EVENT_TEMPLATES[prov])
            event_type, sample_data = template

            # Determine if duplicate
            if duplicate_pool and random.random() < duplicate_rate:
                event_id = random.choice(duplicate_pool)
            else:
                event_id = f"evt_{prov[:3]}_{uuid.uuid4().hex[:12]}"

            # Determine signature validity
            is_invalid_sig = random.random() < invalid_signature_rate

            # Determine fault injection
            fault = None
            if random.random() < failure_rate:
                fault = random.choice(["500", "429", "timeout"])

            async def worker(p, eid, et, d, inv_sig, flt):
                async with semaphore:
                    res = await send_single_event(client, base_url, p, eid, et, d, inv_sig, flt)
                    if res.get("is_accepted"):
                        stats["accepted"] += 1
                    elif res.get("is_duplicate"):
                        stats["duplicates"] += 1
                    elif res.get("is_rejected"):
                        stats["rejected"] += 1
                    else:
                        stats["errors"] += 1
                    if "latency_ms" in res:
                        stats["latencies"].append(res["latency_ms"])

            tasks.append(worker(prov, event_id, event_type, sample_data, is_invalid_sig, fault))

        start_time = time.time()
        await asyncio.gather(*tasks)
        total_time = time.time() - start_time

    avg_lat = sum(stats["latencies"]) / max(1, len(stats["latencies"]))
    print("\n" + "="*50)
    print("🎯 Event Generation Complete Summary")
    print("="*50)
    print(f"Total Sent:        {count}")
    print(f"Time Taken:        {total_time:.2f}s ({count / max(0.001, total_time):.1f} req/s)")
    print(f"✅ Accepted (202): {stats['accepted']}")
    print(f"🔁 Duplicates:     {stats['duplicates']}")
    print(f"🚫 Rejected (HMAC):{stats['rejected']}")
    print(f"❌ Other / Errors: {stats['errors']}")
    print(f"⚡ Avg Ingest Lat:  {avg_lat:.2f}ms")
    print("="*50 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EventForge Synthetic Event Generator")
    parser.add_argument("--count", type=int, default=100, help="Number of events to generate")
    parser.add_argument("--provider", type=str, default="random", choices=["stripe", "razorpay", "github", "generic", "random"])
    parser.add_argument("--concurrency", type=int, default=15, help="Concurrent HTTP workers")
    parser.add_argument("--duplicate-rate", type=float, default=0.05, help="Duplicate probability (0.0 - 1.0)")
    parser.add_argument("--failure-rate", type=float, default=0.05, help="Downstream fault probability")
    parser.add_argument("--invalid-signature-rate", type=float, default=0.02, help="Invalid HMAC probability")
    parser.add_argument("--base-url", type=str, default="http://127.0.0.1:8000", help="EventForge API base URL")

    args = parser.parse_args()
    asyncio.run(generate_events(
        count=args.count,
        provider=args.provider,
        concurrency=args.concurrency,
        duplicate_rate=args.duplicate_rate,
        failure_rate=args.failure_rate,
        invalid_signature_rate=args.invalid_signature_rate,
        base_url=args.base_url
    ))
