# Rheos Failure Handling & Resilience Guide

## 1. Failure Classification

Rheos categorizes all downstream failures into two distinct classes:

| Error Type | Status Codes / Errors | Action |
|---|---|---|
| **RETRYABLE** | HTTP 500, 502, 503, 504, 429, Connection Timeouts, Network Resets | Schedule retry with Exponential Backoff + Jitter |
| **NON_RETRYABLE** | HTTP 400, 401, 403, 404, 422, Schema Violations, Malformed JSON | Direct transition to Dead Letter Queue (DLQ) |

---

## 2. Exponential Backoff with Full Jitter Formula

To avoid thundering herd problems where all retrying workers hammer downstream APIs at identical intervals, Rheos implements the Full Jitter backoff algorithm:

$$\text{Delay} = \min\left(60.0,\, \text{BaseDelay} \times 2^{\text{attempt} - 1} + \text{random}(0.1, \max(0.5, \text{ExponentialDelay} \times 0.2))\right)$$

### Example Schedule (Base = 1.0s):
- **Attempt 1**: ~1.1s – 1.5s
- **Attempt 2**: ~2.1s – 2.6s
- **Attempt 3**: ~4.1s – 4.9s
- **Attempt 4**: ~8.2s – 9.8s
- **Attempt 5**: ~16.5s – 19.5s
- **Attempt 6 (> MAX_RETRIES)**: Transition to Dead Letter Queue

---

## 3. Dead Letter Queue Operations

When an event exceeds `MAX_RETRIES` (default 5) or suffers a fatal non-retryable error, it is recorded in the `dead_letter_events` table with:
- Full original payload and headers
- Exact failure reason and stack trace
- Attempt count history

### DLQ REST Management:
- `GET /api/v1/dlq`: List quarantined events.
- `GET /api/v1/dlq/{dlq_id}`: Inspect stack trace and payload.
- `POST /api/v1/dlq/{dlq_id}/retry`: Replay event back to `events:incoming` with reset attempt count.
- `DELETE /api/v1/dlq/{dlq_id}`: Purge unrecoverable payload.
