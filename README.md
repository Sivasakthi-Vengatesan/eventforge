# Rheos

**Adaptive Event Ingestion, Orchestration, and Fault-Tolerant Delivery Platform**

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Redis Streams](https://img.shields.io/badge/Redis-Streams%20%26%20PEL-DC382D?style=flat-square&logo=redis&logoColor=white)](https://redis.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-ACID%20Persistence-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Multi--Container-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/Tests-33%20Passing-brightgreen?style=flat-square&logo=pytest&logoColor=white)](backend/tests)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

---

## 1. Value Proposition & Problem Scope

**Rheos** is a production-grade distributed event ingestion and processing gateway engineered to eliminate the classic pitfalls of webhook handling: **ingestion timeouts, unhandled burst surges, duplicate transaction charging, and cascading downstream outages**.

In traditional architectures, synchronous webhook handlers process business logic inline, leading to dropped connection errors during downstream latency spikes, repeated webhook retries from providers (e.g., Stripe, Razorpay, GitHub), and catastrophic duplicate state mutations. Rheos decouples high-speed HTTP ingestion ($<10\text{ms}$ budget) from execution via **Redis Streams**, applies **atomic composite idempotency filters**, runs a **closed-loop adaptive policy engine** to throttle or scale workers ($2 \leftrightarrow 8$ cores) dynamically, and isolates poison payloads into an auditable **Dead Letter Queue (DLQ)**.

---

## 2. Key Architectural Highlights

- **Decoupled Asynchronous Ingestion Loop**: Sub-10ms ingestion SLA via FastAPI and non-blocking Redis Streams buffering. Returns `HTTP 202 Accepted` immediately upon cryptographic validation and stream persistence, guaranteeing zero inline execution blocking.
- **Closed-Loop Adaptive Policy Engine**: Continuous telemetry monitor ($Q\text{ depth}$, $L_{p95}\text{ latency}$, $E_{429}\text{ rate limits}$) operating a 4-state finite state machine (`NORMAL`, `PRESSURE`, `DEGRADED`, `RECOVERY`) that dynamically scales worker concurrency and injects selective backpressure.
- **Multi-Tier Priority Routing with Financial Immunity**:
  - `CRITICAL` *(Payment intents, refunds, disputes)*: $0\text{ms}$ delay immunity, dedicated processing lanes, strictly forbidden from batching to preserve ACID isolation.
  - `HIGH` *(Invoices, customer upgrades, GitHub push)*: High-throughput priority routing.
  - `NORMAL` *(Profile updates, subscription lifecycle)*: Standard exponential backoff retry semantics.
  - `LOW` *(Telemetry, audit logs)*: Dynamically throttled and packed into compressed batches during downstream stress.
- **Deterministic Atomic Idempotency Filter**: Composite database constraint on `(provider, event_id)` combined with distributed atomic upserts to ensure exactly-once processing semantics despite aggressive upstream provider retries.
- **Fail-Fast Circuit Breaker & PEL Auto-Claim**: Downstream failure rates exceeding $50\%$ trigger a kinetic circuit breaker (`OPEN`), shedding load without hitting upstream endpoints. Redis Streams Pending Entries List (PEL) auto-claim supervisor automatically rescues orphaned messages if an individual worker node crashes.

---

## 3. Visual Architecture & System Diagrams

### 3.1 End-to-End Distributed Architecture & Event Lifecycle

```mermaid
flowchart TD
    %% Upstream Ingestion Tier
    subgraph IngestionTier["1. Ingestion Gateway (SLA: < 10ms)"]
        direction TB
        PROV["Upstream Webhook Sources<br/><code>Stripe | Razorpay | GitHub | Custom</code>"] -->|HTTPS POST| FASTAPI["FastAPI Ingestion Gateway<br/><code>/api/v1/webhooks/{provider}</code>"]
        FASTAPI --> HMAC{"HMAC-SHA256<br/>Signature Check"}
        HMAC -- Invalid Signature --> REJ_401["HTTP 401 Unauthorized<br/>(Drop & Security Log)"]
        HMAC -- Valid Signature --> IDEMP{"Atomic Idempotency<br/><code>(provider, event_id)</code>"}
        IDEMP -- Duplicate Detected --> DUPE_202["HTTP 202 Duplicate<br/>(No Re-Execution)"]
        IDEMP -- New Event --> CLASSIFY["Priority Classifier<br/><code>CRITICAL | HIGH | NORMAL | LOW</code>"]
    end

    %% Stream Broker Tier
    subgraph BrokerTier["2. Redis Streams Message Broker & Storage"]
        direction TB
        CLASSIFY -->|XADD Stream Payload| RSTREAM[("Redis Streams Engine<br/><code>mystream:events</code>")]
        RSTREAM -.->|Instant Acknowledgment<br/>HTTP 202 Accepted| FASTAPI
        
        PEL_MON["PEL Auto-Claim Supervisor<br/><code>XPENDING / XCLAIM (30s timeout)</code>"] -.->|Rescue Orphaned Events| RSTREAM
    end

    %% Adaptive Control Plane
    subgraph ControlPlane["3. Closed-Loop Adaptive Policy Engine (FSM)"]
        direction TB
        TELEMETRY["Live Telemetry Collector<br/><code>Queue Depth, p95 Latency, 429 Error Rate</code>"] <-->|Real-time Metrics| RSTREAM
        TELEMETRY --> FSM_DECIDE{"Adaptive Policy<br/>FSM Evaluator"}
        
        FSM_DECIDE -->|Normal Load| ST_NORM["NORMAL State<br/>• 4 Workers<br/>• 0ms Delay"]
        FSM_DECIDE -->|Q > 100 or Latency Spike| ST_PRES["PRESSURE State<br/>• Scale to 8 Workers<br/>• 50ms Low-Tier Delay"]
        FSM_DECIDE -->|Downstream 429 > 15%| ST_DEG["DEGRADED State<br/>• Scale to 2 Workers<br/>• 3.0x Backoff Multiplier"]
        FSM_DECIDE -->|Metrics Stabilized| ST_REC["RECOVERY State<br/>• Step-Up Canary Probes<br/>• Drain Lag Safely"]
    end

    %% Distributed Worker Fleet
    subgraph WorkerFleet["4. Elastic Worker Fleet & Circuit Breaker"]
        direction TB
        ST_NORM & ST_PRES & ST_DEG & ST_REC ==>|Actuate Fleet Concurrency| WORKERS["Elastic Async Workers<br/><code>2 ↔ 8 Dynamic Worker Pool</code>"]
        RSTREAM -->|XREADGROUP Consumer Group| WORKERS
        
        WORKERS --> CB_EVAL{"Circuit Breaker<br/>Evaluation"}
        CB_EVAL -- "OPEN (Tripped)" --> CB_FAIL["Fail-Fast Re-Queue<br/>(Cooldown: 5.0s)"]
        CB_EVAL -- "CLOSED / HALF-OPEN" --> DISPATCH["Target Downstream API / Handler<br/><code>POST /api/v1/internal/execute</code>"]
    end

    %% Persistence & Quarantine
    subgraph PersistenceTier["5. ACID Persistence & Dead Letter Queue (DLQ)"]
        direction TB
        DISPATCH -- "HTTP 200/201 OK" --> XACK["XACK Redis Stream"]
        XACK --> DB_AUDIT[("PostgreSQL / SQLite<br/>Audit & Event Ledger")]
        
        DISPATCH -- "HTTP 5xx / 429 Timeout" --> RETRY_ENG["Exponential Jitter Retry Engine<br/><code>t = base * 2^n + jitter(0,1)</code>"]
        RETRY_ENG -->|Retries <= 5| RSTREAM
        RETRY_ENG -- "Retries > 5" --> DLQ_STORE[("Dead Letter Queue (DLQ)<br/>Quarantine Store with Stack Trace")]
        DISPATCH -- "HTTP 400 Bad Schema" --> DLQ_STORE
        
        DLQ_STORE --> REPLAY_TOOL["DLQ Sanitization & Replay Tool<br/><code>POST /api/v1/dlq/{id}/replay</code>"]
        REPLAY_TOOL -.->|Re-Inject Validated Event| RSTREAM
    end

    %% Styling Definitions
    style IngestionTier fill:#1a1c23,stroke:#60a5fa,stroke-width:2px,color:#f3f4f6
    style BrokerTier fill:#1a1c23,stroke:#f59e0b,stroke-width:2px,color:#f3f4f6
    style ControlPlane fill:#1a1c23,stroke:#a78bfa,stroke-width:2px,color:#f3f4f6
    style WorkerFleet fill:#1a1c23,stroke:#34d399,stroke-width:2px,color:#f3f4f6
    style PersistenceTier fill:#1a1c23,stroke:#f87171,stroke-width:2px,color:#f3f4f6
    
    style PROV fill:#2d3748,stroke:#cbd5e1,color:#f8fafc
    style FASTAPI fill:#1e3a8a,stroke:#3b82f6,color:#ffffff
    style RSTREAM fill:#7c2d12,stroke:#ea580c,color:#ffffff
    style WORKERS fill:#064e3b,stroke:#059669,color:#ffffff
    style DB_AUDIT fill:#1e293b,stroke:#38bdf8,color:#ffffff
    style DLQ_STORE fill:#450a0a,stroke:#dc2626,color:#ffffff
```

---

### 3.2 Adaptive Policy Engine State Transitions (FSM)

```mermaid
stateDiagram-v2
    [*] --> NORMAL

    NORMAL --> PRESSURE : Queue Depth > 100 OR Latency p95 > 200ms
    PRESSURE --> NORMAL : Queue Depth < 20 AND Latency p95 < 50ms
    
    NORMAL --> DEGRADED : Downstream 429 Rate > 15% OR Circuit Breaker OPEN
    PRESSURE --> DEGRADED : Downstream 429 Rate > 15% OR Downstream 500s > 25%
    
    DEGRADED --> RECOVERY : 429 Rate == 0% for Cooldown Window (10s)
    RECOVERY --> NORMAL : Canary Probes 100% Succeeded (5 consecutive)
    RECOVERY --> DEGRADED : Canary Probe Failed (429 / 5xx error)

    state NORMAL {
        [*] --> Normal_Config
        Normal_Config : Concurrency = 4 Workers
        Normal_Config : Low-Tier Throttle = 0ms
        Normal_Config : Retry Multiplier = 1.0x
    }

    state PRESSURE {
        [*] --> Pressure_Config
        Pressure_Config : Concurrency = 8 Workers (Scaled Up)
        Pressure_Config : Low-Tier Throttle = 50ms
        Pressure_Config : Batch Low Priority Events
    }

    state DEGRADED {
        [*] --> Degraded_Config
        Degraded_Config : Concurrency = 2 Workers (Shed Load)
        Degraded_Config : Retry Multiplier = 3.0x Backpressure
        Degraded_Config : Pause Non-Critical Ingestion
    }

    state RECOVERY {
        [*] --> Recovery_Config
        Recovery_Config : Concurrency = 3 Workers (Gradual Ramp)
        Recovery_Config : Canary Verification Mode
    }
```

---

### 3.3 Asynchronous Ingestion vs Background Execution Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Provider as Webhook Provider (Stripe/GitHub)
    participant Gateway as FastAPI Ingestion (<10ms)
    participant Redis as Redis Streams (PEL)
    participant FSM as Adaptive Policy Engine
    participant Worker as Elastic Worker Fleet
    participant Downstream as Target Service / API
    participant DB as PostgreSQL Ledger / DLQ

    rect rgb(30, 41, 59)
        Note over Provider, Gateway: Synchronous Ingestion Window (< 10ms budget)
        Provider->>Gateway: POST /api/v1/webhooks/{provider} (HMAC Header + JSON)
        Gateway->>Gateway: Verify HMAC signature (constant-time)
        Gateway->>Gateway: Check Idempotency (provider + event_id)
        Gateway->>Redis: XADD mystream:events (Priority tagged)
        Redis-->>Gateway: Event ID generated (e.g. 1727000000000-0)
        Gateway-->>Provider: HTTP 202 Accepted {"status":"QUEUED","id":"..."}
    end

    rect rgb(20, 83, 45)
        Note over Redis, DB: Asynchronous Worker Execution Loop
        FSM->>Redis: Monitor Queue Depth & Rate Limit Errors
        FSM->>Worker: Tune Concurrency (2 to 8 Workers)
        Worker->>Redis: XREADGROUP Consumer Group (Block 2s)
        Redis-->>Worker: Deliver Event Payload
        Worker->>Worker: Check Downstream Circuit Breaker
        alt Circuit Breaker CLOSED
            Worker->>Downstream: POST /execute (Event Payload)
            alt Success (HTTP 200/201)
                Downstream-->>Worker: HTTP 200 OK
                Worker->>Redis: XACK mystream:events EventID
                Worker->>DB: INSERT into events (Status: COMPLETED)
            else Downstream 429 / 5xx Failure
                Downstream-->>Worker: HTTP 429 Too Many Requests
                Worker->>FSM: Increment 429 Error Counter
                Worker->>Redis: Schedule Retry with Exponential Jitter
            end
        else Max Retries Exceeded (>5 attempts)
            Worker->>DB: INSERT into DLQ (Poison payload + Stack trace)
            Worker->>Redis: XACK mystream:events EventID (Quarantined)
        end
    end
```

---

## 4. Core Design Decisions & Trade-Offs

| Design Area | Decision Selected | Alternative Considered | Technical Rationale & Trade-Off |
|---|---|---|---|
| **Ingestion Protocol** | Async Ingestion Buffer (`HTTP 202`) | Synchronous Execution (`HTTP 200/500`) | Webhook providers enforce strict $5\text{–}10\text{s}$ timeouts. Ingestion decoupling guarantees $<10\text{ms}$ response times, preventing upstream retry storms during heavy database load. |
| **Stream Broker** | Redis Streams with Consumer Groups | Apache Kafka / RabbitMQ | Redis Streams delivers sub-millisecond append latency and built-in Pending Entries List (PEL) for lightweight crash-recovery without the operational footprint of Zookeeper/KRaft clusters. |
| **Idempotency Strategy** | Atomic DB Composite Constraint `(provider, event_id)` | In-Memory TTL Cache | Memory caches lose state upon restarts and fail during distributed race windows. Relational constraints provide true ACID guarantees across concurrent workers. |
| **Concurrency Scaling** | Dynamic Closed-Loop Policy FSM | Static Fixed Concurrency Pools | Static pools either exhaust database connections during surges or starve the queue. The FSM dynamically adjusts worker concurrency ($2 \leftrightarrow 8$) based on active telemetry. |
| **Error Handling** | Circuit Breaker + Exponential Jitter | Indefinite Immediate Retries | Immediate retries exacerbate downstream API rate limits (HTTP 429). Full jitter decorrelates retry spikes, while circuit breaking fails fast to preserve downstream recovery. |

---

## 5. Edge-Case Resilience & Failure Recovery

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          EDGE-CASE RESILIENCE MATRIX                        │
├─────────────────────────┬───────────────────────────────────────────────────┤
│ FAILURE SCENARIO        │ SYSTEM MITIGATION & RECOVERY MECHANISM            │
├─────────────────────────┼───────────────────────────────────────────────────┤
│ Concurrent Duplicate    │ Composite unique database indexing ensures only   │
│ Ingestion Floods        │ 1 record commits; concurrent duplicates receive   │
│                         │ HTTP 202 with DUPLICATE flag and 0 re-execution.  │
├─────────────────────────┼───────────────────────────────────────────────────┤
│ Poison-Pill / Malformed │ Non-retryable structural errors (400 Bad Request) │
│ Payloads                │ bypass retry loops and route immediately to DLQ.  │
├─────────────────────────┼───────────────────────────────────────────────────┤
│ Worker Node Crash /     │ Redis Pending Entries List (PEL) monitor auto-    │
│ Out-of-Memory (OOM)     │ claims abandoned un-ACKed messages after 30s.     │
├─────────────────────────┼───────────────────────────────────────────────────┤
│ Downstream 429 Rate     │ Triggers DEGRADED mode, scales workers to min (2),│
│ Limit Outages           │ and applies 3.0x backpressure retry multiplier.   │
├─────────────────────────┼───────────────────────────────────────────────────┤
│ Broker Temporary        │ Graceful fallback to durable local write-ahead    │
│ Disconnection           │ buffer with reconnect retry loop.                 │
└─────────────────────────┴───────────────────────────────────────────────────┘
```

1. **At-Least-Once Delivery with Idempotent Execution**: Redis Streams consumer groups deliver messages to worker pools with explicit acknowledgment (`XACK`). If a worker dies mid-execution, the unacknowledged message remains in the Pending Entries List (PEL) and is reassigned to healthy workers.
2. **Dead Letter Queue (DLQ) Quarantine**: Malformed payloads, invalid signatures, or events that exceed maximum retry thresholds ($N > 5$) are quarantined in the DLQ with full stack traces, original payload snapshots, and headers for manual inspection or sanitized replay.
3. **Downstream Circuit Breaker**: Tracks a 10-event sliding window. If failure rate exceeds $50\%$, state transitions to `OPEN` for a $5.0\text{s}$ cooldown, immediately rejecting outbound requests with synthetic retry timers to prevent downstream resource starvation.

---

## 6. Performance Benchmarks

*Empirical benchmarking conducted via `scripts/benchmark.py` running on 8 cores, 16GB RAM with 200 randomized mixed-tier webhook payloads:*

| Performance Metric | Static Fixed Pipeline | Rheos Adaptive Engine | Architectural Impact |
|---|---|---|---|
| **Worker Concurrency** | Fixed 2 Workers (Static) | Adaptive ($2 \leftrightarrow 8$ Cores) | Automated Elastic Fleet Scaling |
| **Ingestion Latency (p95)** | $8.40\text{ ms}$ | **$4.12\text{ ms}$** | **$50.9\%$ Faster Ingestion Response** |
| **CRITICAL Event Latency (p95)** | $14,448.41\text{ ms}$ | **$10,532.08\text{ ms}$** | **$27.1\%$ Latency Reduction for Financial Events** |
| **Event Loss Under 429 Storm** | $23.5\%$ Dropped / Timed Out | **$0.00\%$ (Zero Loss)** | **100% Guaranteed Delivery via DLQ / Retries** |
| **Duplicate Transaction Prevention** | Partial (Cache Misses) | **$100\%$ Filtered (0 Duplicates)** | **Strict Composite ACID Enforcement** |

---

## 7. Quickstart & Local Setup

### 7.1 Prerequisites
- **Python**: 3.11+ or 3.12+
- **Node.js**: 18+ & npm (for dashboard UI)
- **Redis & PostgreSQL**: (or Docker Compose for zero-dependency execution)

### 7.2 Option A: Containerized Execution (Recommended)

```bash
# 1. Clone repository
git clone https://github.com/Sivasakthi-Vengatesan/eventforge.git
cd eventforge

# 2. Start full distributed stack (PostgreSQL + Redis + Backend + Frontend)
docker compose up --build -d

# 3. View live services
docker compose ps
```
- **Web Dashboard**: `http://localhost:3000`
- **FastAPI OpenAPI / Swagger Docs**: `http://localhost:8000/docs`
- **Interactive ReDoc**: `http://localhost:8000/redoc`
- **Real-Time Telemetry Stream**: `ws://localhost:8000/ws/monitor`

### 7.3 Option B: Local Development Setup

```bash
# 1. Setup Backend Environment
cd backend
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure Environment Variables
cp .env.example .env

# 4. Launch FastAPI Control Plane & Worker Fleet
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

```bash
# 5. Launch Frontend Console (In a separate terminal)
cd frontend
npm install
npm run dev
```

### 7.4 Running Automated Verification & Chaos Suites

```bash
# Run unit, integration, and concurrency test suites (33 tests)
python -m pytest backend/tests -v

# Run 10-scenario chaos engineering simulation
python scripts/chaos_test.py --scenario all

# Run head-to-head empirical benchmark
python scripts/benchmark.py --events 200
```

---

## 8. API & Event Contract Reference

### 8.1 Ingestion & Webhook Endpoints

| HTTP Method | Route | Request Payload / Contract | Response Code | System Behavior |
|---|---|---|---|---|
| `POST` | `/api/v1/webhooks/{provider}` | Raw JSON body + HMAC Signature Header (`stripe-signature`, `x-hub-signature-256`, `x-razorpay-signature`) | `202 Accepted`<br/>`401 Unauthorized`<br/>`400 Bad Request` | Verifies HMAC, applies composite idempotency filter, prioritizes event, and pushes payload to Redis Stream. |
| `GET` | `/api/v1/events` | Query: `status`, `priority`, `provider`, `limit`, `offset` | `200 OK` | Retrieves paginated historical event log and execution lifecycle statuses. |
| `GET` | `/api/v1/events/{event_id}` | Path: `event_id` (str) | `200 OK` / `404 Not Found` | Fetches full event lifecycle audit trail, payload snapshot, and retry attempts. |

### 8.2 Control Plane, Workers & DLQ Endpoints

| HTTP Method | Route | Request Payload / Contract | Response Code | System Behavior |
|---|---|---|---|---|
| `GET` | `/api/v1/workers` | None | `200 OK` | Retrieves active worker fleet status, core count, and current job allocations. |
| `POST` | `/api/v1/workers/scale` | JSON: `{"worker_count": 8}` | `200 OK` / `400 Bad Request` | Manually scales worker concurrency pool between limits (1 to 16 cores). |
| `GET` | `/api/v1/dlq` | Query: `limit`, `offset` | `200 OK` | Retrieves all quarantined poison-pill events with error traces. |
| `POST` | `/api/v1/dlq/{dlq_id}/replay`| Path: `dlq_id` (str) | `200 OK` / `404 Not Found` | Re-queues a quarantined event with sanitized schema payload for execution. |
| `DELETE` | `/api/v1/dlq/{dlq_id}` | Path: `dlq_id` (str) | `200 OK` / `404 Not Found` | Permanently deletes a poison record from the quarantine ledger. |
| `GET` | `/api/v1/metrics/system` | None | `200 OK` | Fetches live latency histograms, queue depth, throughput, and error rates. |
| `GET` | `/api/v1/policies` | None | `200 OK` | Inspects current Adaptive Policy Engine FSM state and operational parameters. |
| `PUT` | `/api/v1/policies/{id}` | JSON: `{"value": "<new_val>"}` | `200 OK` | Updates dynamic threshold parameters (e.g., queue pressure triggers). |
| `WS` | `/ws/monitor` | WebSocket Upgrade | `101 Switching Protocols` | Continuous bi-directional telemetry broadcast to monitoring consoles. |

---

## 9. License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for details.
