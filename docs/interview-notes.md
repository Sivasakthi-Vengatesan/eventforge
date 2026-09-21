# Rheos — Staff Distributed Systems & Reliability Engineering Interview Guide

> **Deep-Dive Technical Rationales, Invariants, Failure Modes, and System Design Trade-Offs**

---

## 1. Core System Design Questions & Answers

### Q1: Why decouple ingestion (`<10ms`) from processing instead of executing business logic in the HTTP request?
**Answer**:
Upstream webhook dispatchers (Stripe, GitHub, Shopify) enforce strict HTTP timeout limits (typically 5–10s). If your gateway performs database queries, downstream API calls, or email dispatch in the HTTP request cycle:
1. Any downstream latency spike causes the upstream provider to time out and retry.
2. The retries multiply traffic volume, creating a self-inflicted Distributed Denial of Service (DDoS) storm.
3. Decoupling ingestion with an immediate `HTTP 202 Accepted` after appending to a durable stream (Redis Streams / Kafka) bounds ingestion latency to `<10ms`, completely insulating the upstream webhook provider from downstream issues.

---

### Q2: How do you achieve exactly-once processing semantics in a distributed webhook platform?
**Answer**:
In distributed systems over networks that can partition or drop packets, true physical "exactly-once delivery" is impossible due to the Two Generals' Problem. 

Instead, Rheos implements **at-least-once delivery with strictly idempotent consumer execution**:
1. **At-least-once delivery**: Workers read from Redis Streams via Consumer Groups and only emit `XACK` *after* the database transaction commits and downstream processing completes.
2. **Idempotency Filter**: Ingestion checks an atomic composite unique constraint `(provider, event_id)` in the ACID database. Duplicate events are flagged, incremented, and returned with `HTTP 202 {"status": "DUPLICATE"}` without queuing duplicate work.
3. **Downstream Idempotency Keys**: Workers supply unique idempotency tokens to all external mutation APIs.

---

### Q3: Why must financial events (`CRITICAL`) bypass batching and backpressure?
**Answer**:
Batching multiple events into a single downstream database transaction or HTTP payload introduces **fate-sharing**:
- If 1 event out of a 10-event batch fails due to a schema mismatch or invalid card token, either the entire batch rolls back (delaying 9 valid transactions) or complex partial-commit reconciliation logic is required.
- For financial webhooks (`payment_intent.succeeded`, `charge.refunded`), individual ACID isolation and sub-100ms processing SLAs are mandatory. 
- Low-priority events (`analytics.tracked`, `audit.log`) can tolerate batching in chunks of 10 during pressure modes because individual message delivery latency is non-critical.

---

### Q4: How does Redis Streams Pending Entries List (PEL) prevent message loss during worker crashes?
**Answer**:
When a worker reads a message via `XREADGROUP`, Redis places that message into the consumer group's **Pending Entries List (PEL)**. The message is NOT removed from the stream.
- If the worker process crashes (SIGKILL, OOM, hardware failure) before calling `XACK`, the message remains in the PEL with an advancing idle time.
- The Rheos `WorkerManager` periodically inspects `XPENDING`. Any message unacknowledged for $>30\text{s}$ is claimed via `XCLAIM` and assigned to a healthy worker, ensuring zero message loss.

---

### Q5: What is the thundering herd problem in retry systems and how does Rheos eliminate it?
**Answer**:
When a downstream service suffers a temporary outage (e.g., 500 error), naive retry implementations wait a fixed interval (e.g., 2.0s) and retry all failed requests simultaneously. This creates massive synchronized traffic spikes (thundering herds) that repeatedly crash the recovering service.

Rheos eliminates this through three combined mechanisms:
1. **Full Jitter Exponential Backoff**:
   $$t_{\text{backoff}} = \text{random}(0, \, \text{base\_delay} \cdot 2^{\text{attempt}} \cdot \mu_{\text{mode}})$$
   Decorrelating retry timestamps flattens traffic spikes into a uniform distribution.
2. **Adaptive Mode Multipliers**: When downstream 429 rate limits exceed 15%, the system transitions to `DEGRADED` mode, tripling the backoff multiplier ($\mu = 3.0\times$) to grant the downstream service room to breathe.
3. **Downstream Circuit Breaker**: If failures exceed 5 consecutive errors, the circuit trips `OPEN`, failing fast locally with $0\text{ms}$ delay and **zero downstream network calls** until the cooldown window expires.

---

## 2. Distributed Architecture Trade-Off Matrix

| Dimension | Redis Streams | Apache Kafka | RabbitMQ |
| :--- | :--- | :--- | :--- |
| **Ingestion Latency** | **Sub-millisecond** (In-memory + AOF) | 5–15ms (Disk-buffered OS page cache) | 1–5ms (Erlang Actor queue) |
| **Message Ordering** | Strict per-stream | Strict per-partition | Strict per-queue |
| **Storage Overhead** | RAM bound (Eviction / Trimming needed) | Disk bound (Petabyte scale retention) | RAM / Disk hybrid |
| **Operational Simplicity**| Extremely lightweight (Embedded or single binary) | High (Zookeeper / KRaft cluster) | Moderate (Erlang runtime cluster) |
| **Rheos Fit** | **Optimal** for high-throughput webhook gateway | Heavyweight for single-region services | Less native consumer group stream semantics |

---

## 3. Key Distributed Systems Concepts Demonstrated in Code

- **Actor Model / Worker Fleet**: Dynamic scaling ($2 \leftrightarrow 8$) in `backend/app/workers/manager.py`.
- **Closed-Loop Feedback Control**: Proportional-derivative state transitions in `backend/app/adaptive/policy_rules.py`.
- **Finite State Machine (FSM)**: 3-state Circuit Breaker (`CLOSED`, `OPEN`, `HALF_OPEN`) in `backend/app/services/circuit_breaker.py`.
- **Cryptographic Security**: HMAC-SHA256 constant-time digest comparison in `backend/app/security/hmac.py`.
- **Idempotency & Replay Attack Defense**: In `backend/app/services/idempotency.py`.
