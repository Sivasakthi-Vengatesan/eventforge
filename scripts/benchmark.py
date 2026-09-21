"""
Rheos Static vs. Adaptive Empirical Benchmark Suite
Runs identical workload streams under normal and failure conditions and measures real metrics.
"""

import sys
import os
import time
import json
import asyncio
import argparse
import random
import httpx
from datetime import datetime, timezone

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.config import settings
from backend.app.security.hmac import generate_stripe_signature

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000"

def get_stripe_headers(payload_bytes: bytes) -> dict:
    sig = generate_stripe_signature(payload_bytes, settings.WEBHOOK_SECRET_STRIPE)
    return {
        "Content-Type": "application/json",
        "stripe-signature": sig
    }

async def send_single_event(client: httpx.AsyncClient, i: int, failure_rate: float):
    is_crit = (i % 5 == 0)
    priority = "CRITICAL" if is_crit else "NORMAL"
    evt_type = "payment.failed" if is_crit else "order.updated"
    fault = "500" if (random.random() < failure_rate) else None
    
    payload = {
        "id": f"evt_bench_{i}_{int(time.time()*1000)}",
        "type": evt_type,
        "priority": priority,
        "data": {"amount": random.randint(100, 9999)}
    }
    body_bytes = json.dumps(payload).encode("utf-8")
    headers = get_stripe_headers(body_bytes)
    if fault:
        headers["x-mock-fault"] = fault
    
    t0 = time.perf_counter()
    try:
        res = await client.post(f"{BASE_URL}/api/v1/webhooks/stripe", content=body_bytes, headers=headers)
        lat = (time.perf_counter() - t0) * 1000
        status = res.json().get("status") if res.status_code == 202 else "ERROR"
        return {"priority": priority, "latency": lat, "status_code": res.status_code, "status": status}
    except Exception:
        lat = (time.perf_counter() - t0) * 1000
        return {"priority": priority, "latency": lat, "status_code": 500, "status": "ERROR"}

async def run_workload(client: httpx.AsyncClient, count: int, failure_rate: float = 0.10) -> dict:
    """Dispatches a stream of mixed priority events concurrently and measures latencies."""
    start_time = time.perf_counter()
    
    tasks = [send_single_event(client, i, failure_rate) for i in range(count)]
    results = await asyncio.gather(*tasks)

    critical_latencies = [r["latency"] for r in results if r["priority"] == "CRITICAL"]
    normal_latencies = [r["latency"] for r in results if r["priority"] != "CRITICAL"]
    success_count = sum(1 for r in results if r["status"] == "ACCEPTED")
    duplicate_count = sum(1 for r in results if r["status"] == "DUPLICATE")
    error_count = sum(1 for r in results if r["status"] == "ERROR")

    total_duration = time.perf_counter() - start_time
    throughput = round(count / max(0.001, total_duration), 1)

    crit_p95 = round(sorted(critical_latencies)[int(len(critical_latencies) * 0.95)], 2) if critical_latencies else 0.0
    norm_p95 = round(sorted(normal_latencies)[int(len(normal_latencies) * 0.95)], 2) if normal_latencies else 0.0

    return {
        "event_count": count,
        "duration_seconds": round(total_duration, 2),
        "throughput_req_per_sec": throughput,
        "critical_p95_ms": crit_p95,
        "normal_p95_ms": norm_p95,
        "success_count": success_count,
        "duplicate_count": duplicate_count,
        "error_count": error_count,
    }

async def main():
    parser = argparse.ArgumentParser(description="Rheos Benchmark")
    parser.add_argument("--events", type=int, default=200, help="Number of benchmark events")
    args = parser.parse_args()

    print("=========================================================================")
    print("        RHEOS EMPIRICAL BENCHMARK: STATIC vs. ADAPTIVE MODE              ")
    print("=========================================================================")
    print(f"Workload: {args.events} Mixed Events | Ingestion Budget: <10ms | Target: 127.0.0.1:8000\n")

    async with httpx.AsyncClient(timeout=15.0) as client:
        # Check backend
        try:
            h = await client.get(f"{BASE_URL}/api/v1/health")
            if h.status_code != 200:
                print("Backend unavailable. Please start backend first.")
                return
        except Exception as e:
            print(f"Error connecting to backend: {e}")
            return

        # 1. Benchmark in STATIC Mode (Fixed workers, normal FIFO)
        print("[1/2] Executing Benchmark under STATIC Policy...")
        await client.post(f"{BASE_URL}/api/v1/policies/mode", json={"mode": "NORMAL", "reason": "Benchmark Static Mode"})
        await client.post(f"{BASE_URL}/api/v1/downstream/config", json={"fault": None, "reset_circuit_breaker": True})
        await asyncio.sleep(1)
        
        static_results = await run_workload(client, count=args.events, failure_rate=0.08)
        print(f"-> Static Completed: Throughput={static_results['throughput_req_per_sec']} req/s | Crit P95={static_results['critical_p95_ms']}ms")

        await asyncio.sleep(2)

        # 2. Benchmark in ADAPTIVE Mode (Priority routing, backpressure, dynamic concurrency)
        print("\n[2/2] Executing Benchmark under ADAPTIVE Policy (Pressure + 429 Fault)...")
        await client.post(f"{BASE_URL}/api/v1/policies/mode", json={"mode": "PRESSURE", "reason": "Benchmark Adaptive Mode"})
        await asyncio.sleep(1)
        
        adaptive_results = await run_workload(client, count=args.events, failure_rate=0.15)
        print(f"-> Adaptive Completed: Throughput={adaptive_results['throughput_req_per_sec']} req/s | Crit P95={adaptive_results['critical_p95_ms']}ms")

        # Restore Normal State
        await client.post(f"{BASE_URL}/api/v1/policies/mode", json={"mode": "NORMAL", "reason": "Benchmark completed"})
        await client.post(f"{BASE_URL}/api/v1/downstream/config", json={"fault": None, "reset_circuit_breaker": True})

        # Summary Comparison Table
        print("\n=========================================================================")
        print("                      BENCHMARK COMPARISON MATRIX                        ")
        print("=========================================================================")
        print(f"{'Metric':<32} | {'Static Mode':<18} | {'Adaptive Mode':<18}")
        print("-" * 73)
        print(f"{'Workload Batch Size':<32} | {static_results['event_count']:<18} | {adaptive_results['event_count']:<18}")
        print(f"{'Total Execution Duration':<32} | {str(static_results['duration_seconds']) + 's':<18} | {str(adaptive_results['duration_seconds']) + 's':<18}")
        print(f"{'Ingestion Throughput':<32} | {str(static_results['throughput_req_per_sec']) + ' req/s':<18} | {str(adaptive_results['throughput_req_per_sec']) + ' req/s':<18}")
        print(f"{'CRITICAL Priority P95 Latency':<32} | {str(static_results['critical_p95_ms']) + ' ms':<18} | {str(adaptive_results['critical_p95_ms']) + ' ms':<18}")
        print(f"{'NORMAL Priority P95 Latency':<32} | {str(static_results['normal_p95_ms']) + ' ms':<18} | {str(adaptive_results['normal_p95_ms']) + ' ms':<18}")
        print(f"{'Successful Ingestions':<32} | {static_results['success_count']:<18} | {adaptive_results['success_count']:<18}")
        print(f"{'Duplicate Interceptions':<32} | {static_results['duplicate_count']:<18} | {adaptive_results['duplicate_count']:<18}")
        print("=========================================================================\n")

        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        # Save results to data/benchmark_results.json
        output_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_count": args.events,
            "static_mode": static_results,
            "adaptive_mode": adaptive_results
        }
        with open("data/benchmark_results.json", "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)
        print("Benchmark results saved to data/benchmark_results.json")

if __name__ == "__main__":
    asyncio.run(main())
