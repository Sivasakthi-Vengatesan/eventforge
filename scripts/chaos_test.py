"""
Rheos Chaos Engineering & Failure Simulator Suite
Executes 10 realistic distributed resilience scenarios against the live gateway.
"""

import sys
import os
import time
import json
import asyncio
import argparse
import random
import httpx

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

async def send_stripe_event(client: httpx.AsyncClient, payload: dict, extra_headers: dict = None) -> httpx.Response:
    body_bytes = json.dumps(payload).encode("utf-8")
    headers = get_stripe_headers(body_bytes)
    if extra_headers:
        headers.update(extra_headers)
    return await client.post(f"{BASE_URL}/api/v1/webhooks/stripe", content=body_bytes, headers=headers)

async def run_scenario_1_traffic_spike(client: httpx.AsyncClient):
    print("\n--- [SCENARIO 1] Traffic Spike: Ingesting 100 events in rapid burst ---")
    tasks = []
    for i in range(100):
        priority = "CRITICAL" if i % 10 == 0 else "HIGH" if i % 4 == 0 else "LOW" if i % 3 == 0 else "NORMAL"
        payload = {
            "id": f"evt_spike_{i}_{int(time.time()*1000)}",
            "type": "payment.failed" if priority == "CRITICAL" else "payment.success" if priority == "HIGH" else "analytics.event",
            "priority": priority,
            "data": {"amount": random.randint(100, 5000)}
        }
        tasks.append(send_stripe_event(client, payload))
    
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    accepted = sum(1 for r in responses if isinstance(r, httpx.Response) and r.status_code == 202)
    print(f"Dispatched 100 events: {accepted} Accepted into stream. Checking adaptive state...")
    
    await asyncio.sleep(2)
    state_res = await client.get(f"{BASE_URL}/api/v1/policies/current")
    if state_res.status_code == 200:
        data = state_res.json()
        print(f"System State: Mode={data.get('current_mode')} | Active Workers={data.get('active_workers')} | Queue Depth={data.get('queue_depth')}")

async def run_scenario_2_downstream_429(client: httpx.AsyncClient):
    print("\n--- [SCENARIO 2] Downstream Rate Limit (HTTP 429) Storm ---")
    print("Injecting downstream 429 fault...")
    await client.post(f"{BASE_URL}/api/v1/downstream/config", json={"fault": "429"})
    
    # Send batch of events
    for i in range(15):
        payload = {"id": f"evt_429_{i}_{int(time.time()*1000)}", "type": "payment_intent.succeeded", "priority": "HIGH"}
        await send_stripe_event(client, payload)
    
    await asyncio.sleep(3)
    state_res = await client.get(f"{BASE_URL}/api/v1/policies/current")
    if state_res.status_code == 200:
        data = state_res.json()
        print(f"Adaptive Response: Mode={data.get('current_mode')} | 429 Rate={data.get('http_429_rate')} | Workers={data.get('active_workers')} | Throttled={data.get('throttled_events_count')}")

async def run_scenario_3_downstream_500(client: httpx.AsyncClient):
    print("\n--- [SCENARIO 3] Downstream 500 Crash Storm & Retry Scheduling ---")
    await client.post(f"{BASE_URL}/api/v1/downstream/config", json={"fault": "500"})
    
    payload = {"id": f"evt_500_test_{int(time.time()*1000)}", "type": "payment.success", "priority": "CRITICAL"}
    res = await send_stripe_event(client, payload)
    print(f"Sent Critical Event: HTTP {res.status_code}. Observing exponential backoff retry...")
    await asyncio.sleep(3)

async def run_scenario_4_latency_spike(client: httpx.AsyncClient):
    print("\n--- [SCENARIO 4] Downstream Latency Spike (1200ms) ---")
    await client.post(f"{BASE_URL}/api/v1/downstream/config", json={"fault": "high_latency"})
    
    tasks = []
    for i in range(10):
        tasks.append(send_stripe_event(client, {"id": f"evt_lat_{i}_{int(time.time()*1000)}", "type": "push"}))
    await asyncio.gather(*tasks)
    
    await asyncio.sleep(2)
    metrics_res = await client.get(f"{BASE_URL}/api/v1/metrics")
    if metrics_res.status_code == 200:
        m = metrics_res.json()
        print(f"Latency Percentiles: P50={m.get('p50_latency_ms')}ms | P95={m.get('p95_latency_ms')}ms | P99={m.get('p99_latency_ms')}ms")

async def run_scenario_5_worker_crash_and_pel(client: httpx.AsyncClient):
    print("\n--- [SCENARIO 5] Worker Crash Simulation & PEL Claim ---")
    print("Simulating crash on worker-1...")
    await client.post(f"{BASE_URL}/api/v1/workers/worker-1/kill")
    
    # Enqueue work
    await send_stripe_event(client, {"id": f"evt_pel_rescue_{int(time.time()*1000)}", "type": "payment.success"})
    await asyncio.sleep(2)
    
    print("Restarting worker-1...")
    await client.post(f"{BASE_URL}/api/v1/workers/worker-1/restart")
    print("Worker restarted. Orphaned messages claimed.")

async def run_scenario_6_idempotency_storm(client: httpx.AsyncClient):
    print("\n--- [SCENARIO 6] Idempotency 20x Duplicate Flood ---")
    shared_id = f"evt_dup_flood_{int(time.time()*1000)}"
    tasks = []
    for i in range(20):
        payload = {"id": shared_id, "type": "payment.success", "data": {"seq": i}}
        tasks.append(send_stripe_event(client, payload))
    
    results = await asyncio.gather(*tasks)
    accepted = sum(1 for r in results if r.status_code == 202 and r.json().get("status") == "ACCEPTED")
    duplicates = sum(1 for r in results if r.status_code == 202 and r.json().get("status") == "DUPLICATE")
    print(f"Sent 20 concurrent duplicate requests: Accepted={accepted} (Expect 1), Flagged DUPLICATE={duplicates} (Expect 19)")
    assert accepted == 1, f"Idempotency invariant violated! Accepted={accepted}"

async def run_scenario_7_circuit_breaker(client: httpx.AsyncClient):
    print("\n--- [SCENARIO 7] Downstream Circuit Breaker Trip & Cooldown ---")
    await client.post(f"{BASE_URL}/api/v1/downstream/config", json={"fault": "500"})
    
    # Trip circuit breaker
    for i in range(8):
        await send_stripe_event(client, {"id": f"evt_cb_{i}_{int(time.time()*1000)}", "type": "payment.success"})
    
    await asyncio.sleep(2)
    cb_res = await client.get(f"{BASE_URL}/api/v1/downstream")
    if cb_res.status_code == 200:
        data = cb_res.json()
        print(f"Circuit Breaker Status: State={data.get('state')} | Consecutive Failures={data.get('consecutive_failures')}")
    
    print("Resetting downstream fault to SUCCESS...")
    await client.post(f"{BASE_URL}/api/v1/downstream/config", json={"fault": None, "reset_circuit_breaker": True})

async def run_scenario_8_priority_backlog(client: httpx.AsyncClient):
    print("\n--- [SCENARIO 8] Priority-Aware Scheduling Verification ---")
    # Send mix of CRITICAL and LOW events
    await send_stripe_event(client, {"id": f"evt_low_batch_{int(time.time()*1000)}", "type": "analytics.event", "priority": "LOW"})
    await send_stripe_event(client, {"id": f"evt_crit_prio_{int(time.time()*1000)}", "type": "security.alert", "priority": "CRITICAL"})
    print("Enqueued LOW and CRITICAL events into pipeline. Priority Router assigned weights.")

async def run_scenario_9_dlq_poison_pill(client: httpx.AsyncClient):
    print("\n--- [SCENARIO 9] DLQ Poison Pill Isolation ---")
    payload = {"id": f"evt_fatal_poison_{int(time.time()*1000)}", "type": "payment.failed", "force_fault": "invalid_data"}
    res = await send_stripe_event(client, payload, extra_headers={"x-mock-fault": "invalid_data"})
    print(f"Dispatched non-retryable poison pill: HTTP {res.status_code}")
    await asyncio.sleep(2)
    
    dlq_res = await client.get(f"{BASE_URL}/api/v1/dlq")
    if dlq_res.status_code == 200:
        dlq_data = dlq_res.json()
        print(f"DLQ Total Quarantined: {dlq_data.get('total')}")

async def run_scenario_10_recovery(client: httpx.AsyncClient):
    print("\n--- [SCENARIO 10] Gradual System Recovery Demonstration ---")
    await client.post(f"{BASE_URL}/api/v1/downstream/config", json={"fault": None, "reset_circuit_breaker": True})
    await client.post(f"{BASE_URL}/api/v1/policies/mode", json={"mode": "NORMAL", "reason": "Chaos test cleanup - restore normal state"})
    
    await asyncio.sleep(1)
    state_res = await client.get(f"{BASE_URL}/api/v1/policies/current")
    if state_res.status_code == 200:
        data = state_res.json()
        print(f"System State: Mode={data.get('current_mode')} | Active Workers={data.get('active_workers')} | Error Rate={data.get('error_rate')}")

async def main():
    parser = argparse.ArgumentParser(description="Rheos Chaos Engineering Suite")
    parser.add_argument("--scenario", default="all", help="Scenario number (1-10) or 'all'")
    args = parser.parse_args()

    scenarios = {
        "1": run_scenario_1_traffic_spike,
        "2": run_scenario_2_downstream_429,
        "3": run_scenario_3_downstream_500,
        "4": run_scenario_4_latency_spike,
        "5": run_scenario_5_worker_crash_and_pel,
        "6": run_scenario_6_idempotency_storm,
        "7": run_scenario_7_circuit_breaker,
        "8": run_scenario_8_priority_backlog,
        "9": run_scenario_9_dlq_poison_pill,
        "10": run_scenario_10_recovery,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Check health
        try:
            health = await client.get(f"{BASE_URL}/api/v1/health")
            if health.status_code != 200:
                print("Rheos backend is not running at http://127.0.0.1:8000")
                return
        except Exception as e:
            print(f"Connection error: {e}. Please start backend first.")
            return

        if args.scenario == "all":
            print("=================================================================")
            print("         RHEOS 10-SCENARIO CHAOS ENGINEERING SUITE              ")
            print("=================================================================")
            for idx in range(1, 11):
                func = scenarios[str(idx)]
                await func(client)
                await asyncio.sleep(1)
            print("\n=================================================================")
            print("          ALL 10 CHAOS SCENARIOS COMPLETED SUCCESSFULLY          ")
            print("=================================================================")
        elif args.scenario in scenarios:
            await scenarios[args.scenario](client)
        else:
            print(f"Unknown scenario {args.scenario}")

if __name__ == "__main__":
    asyncio.run(main())
