import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import argparse
import asyncio
import json
import statistics
import time
import uuid
import httpx
from backend.app.security.hmac import generate_stripe_signature

async def run_load_test(
    count: int = 1000,
    concurrency: int = 50,
    base_url: str = "http://127.0.0.1:8000"
):
    print("\n" + "="*60)
    print("🔥 Rheos High-Throughput Load Benchmark")
    print("="*60)
    print(f"Target URL:         {base_url}/api/v1/webhooks/stripe")
    print(f"Total Requests:     {count}")
    print(f"Concurrency:        {concurrency}")
    print("="*60)

    secret = "whsec_stripe_test_secret_38472948"
    semaphore = asyncio.Semaphore(concurrency)
    latencies = []
    status_codes = {}

    async with httpx.AsyncClient(timeout=15.0, limits=httpx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency)) as client:
        async def send_req(i):
            event_id = f"evt_bench_{uuid.uuid4().hex[:14]}"
            payload_dict = {
                "id": event_id,
                "type": "payment_intent.succeeded",
                "data": {"amount": 5000, "currency": "usd", "index": i}
            }
            body_bytes = json.dumps(payload_dict).encode("utf-8")
            sig = generate_stripe_signature(body_bytes, secret)
            headers = {"Content-Type": "application/json", "Stripe-Signature": sig}

            async with semaphore:
                t0 = time.time()
                try:
                    resp = await client.post(f"{base_url}/api/v1/webhooks/stripe", content=body_bytes, headers=headers)
                    dur_ms = (time.time() - t0) * 1000
                    latencies.append(dur_ms)
                    code = resp.status_code
                    status_codes[code] = status_codes.get(code, 0) + 1
                except Exception as e:
                    dur_ms = (time.time() - t0) * 1000
                    latencies.append(dur_ms)
                    status_codes["ERR"] = status_codes.get("ERR", 0) + 1

        print("⚡ Ingestion phase starting...")
        start_time = time.time()
        tasks = [send_req(i) for i in range(count)]
        await asyncio.gather(*tasks)
        total_time = time.time() - start_time

    # Calculate statistics
    latencies_sorted = sorted(latencies)
    n = len(latencies_sorted)
    p50 = latencies_sorted[int(n * 0.50)] if n else 0
    p95 = latencies_sorted[min(n - 1, int(n * 0.95))] if n else 0
    p99 = latencies_sorted[min(n - 1, int(n * 0.99))] if n else 0
    avg = sum(latencies) / max(1, n)
    rps = count / max(0.001, total_time)

    # Poll backend metrics
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            m_resp = await client.get(f"{base_url}/api/v1/metrics")
            metrics_data = m_resp.json()
    except Exception:
        metrics_data = {}

    print("\n" + "="*60)
    print("📊 BENCHMARK RESULTS")
    print("="*60)
    print(f"Total Requests Sent:       {count}")
    print(f"Total Time Taken:          {total_time:.3f} s")
    print(f"Ingestion Throughput:      {rps:.2f} req/sec")
    print(f"Status Code Breakdown:     {status_codes}")
    print("-"*60)
    print("⏱️  LATENCY PERCENTILES (INGESTION)")
    print(f"   Average Latency:        {avg:.2f} ms")
    print(f"   P50 (Median):           {p50:.2f} ms")
    print(f"   P95:                    {p95:.2f} ms")
    print(f"   P99:                    {p99:.2f} ms")
    print("-"*60)
    print("🔍 BACKEND TELEMETRY SNAPSHOT")
    print(f"   Active Workers:         {metrics_data.get('active_workers', 'N/A')}")
    print(f"   Queue Depth:            {metrics_data.get('queue_depth', 'N/A')}")
    print(f"   Success Rate:           {metrics_data.get('success_rate', 'N/A')}%")
    print(f"   Total Processed (DB):   {metrics_data.get('total_events', 'N/A')}")
    print("="*60 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rheos Load Benchmark")
    parser.add_argument("--count", type=int, default=1000, help="Number of requests")
    parser.add_argument("--concurrency", type=int, default=50, help="Concurrency level")
    parser.add_argument("--base-url", type=str, default="http://127.0.0.1:8000", help="API URL")
    args = parser.parse_args()

    asyncio.run(run_load_test(count=args.count, concurrency=args.concurrency, base_url=args.base_url))
