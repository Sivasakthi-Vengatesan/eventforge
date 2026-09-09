# EventForge API Reference

## Base URLs
- **HTTP**: `http://localhost:8000/api/v1`
- **WebSocket**: `ws://localhost:8000/ws/monitor`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`

---

## Webhook Ingestion

### `POST /api/v1/webhooks/{provider}`
Accepts incoming webhook payloads, validates HMAC signatures, checks idempotency, pushes to Redis Streams, and returns `HTTP 202 Accepted`.

- **Path Parameters**:
  - `provider`: `stripe` | `razorpay` | `github` | `generic`
- **Headers**:
  - Stripe: `Stripe-Signature: t=timestamp,v1=signature_hash`
  - Razorpay: `X-Razorpay-Signature: signature_hash`
  - GitHub: `X-Hub-Signature-256: sha256=signature_hash`, `X-GitHub-Event: push`
  - Generic: `X-Signature-256: signature_hash`
- **Response `202 Accepted`**:
```json
{
  "status": "ACCEPTED",
  "event_id": "evt_str_123456",
  "provider": "stripe",
  "event_type": "payment_intent.succeeded",
  "received_at": "2026-09-09T20:00:00.000Z",
  "message": "Webhook accepted, validated, and queued for asynchronous processing."
}
```

---

## Events Explorer

### `GET /api/v1/events`
Query and filter processed webhook events.
- **Query Parameters**:
  - `provider`: Filter by provider
  - `status`: `QUEUED` | `PROCESSING` | `SUCCESS` | `RETRYING` | `FAILED` | `DLQ` | `DUPLICATE`
  - `search`: Search by event ID
  - `page`: Page number (default: 1)
  - `page_size`: Results per page (default: 50)

### `GET /api/v1/events/{event_id}`
Returns complete event metadata along with chronological attempt execution logs.

---

## Dead Letter Queue (DLQ)

### `GET /api/v1/dlq`
Lists unrecoverable quarantined events.

### `POST /api/v1/dlq/{dlq_id}/retry`
Replays a DLQ event back into Redis Streams for reprocessing.

### `DELETE /api/v1/dlq/{dlq_id}`
Purges a DLQ record.

---

## Metrics & Observability

### `GET /api/v1/metrics`
Returns real-time telemetry (throughput, P50/P95/P99 latency, success rate, queue depth, worker counts).

### `GET /api/v1/health`
Checks PostgreSQL, Redis, and Worker fleet health.

### `WS /ws/monitor`
WebSocket stream broadcasting:
- `METRICS_UPDATE` (every 1s)
- `EVENT_RECEIVED`
- `EVENT_STATUS_CHANGED`
- `EVENT_DUPLICATE_RECEIVED`
- `WORKER_UPDATED`
