# EventForge ◆

### Adaptive Event Reliability & Distributed Processing Platform

> **Accept in `<10ms`, process safely, prevent duplicate charges, autonomously adapt to downstream pressure, and observe everything in real time.**

---

## ⚡ What is EventForge?

**EventForge** is a production-grade distributed event ingestion and processing gateway. It decouples high-speed asynchronous ingestion from backend processing and introduces an **Adaptive Event Policy Engine** that dynamically adjusts system behavior based on queue depth, downstream failure rates, HTTP 429 rate limits, and event priority classifications.

```
[ Upstream Webhooks ] (Stripe, GitHub, Razorpay, Generic)
       │ HTTP POST (Measured <10ms Budget)
       ▼
[ FastAPI Ingestion Gateway ]
       ├── 1. HMAC-SHA256 Cryptographic Verification (Constant-time + Replay Window)
       ├── 2. Atomic Idempotency Filter (DB Uniqueness Constraint + Atomic Upsert)
       └── 3. Priority Classifier (CRITICAL, HIGH, NORMAL, LOW)
       │
       ▼ (Zero in-flight processing)
[ Redis Streams Broker / In-Memory Queue ] ◄── (HTTP 202 Accepted)
       │
       ├───────────────────────────────────────────┐
       ▼                                           ▼
[ Adaptive Policy Control Loop ]          [ Consumer Group Fleet ]
  - Real-Time Telemetry Monitor             - Worker Fleet (2 ↔ 8 Cores Elastic)
  - Finite State Machine (4 Modes)          - Priority Channel Routing
  - Dynamic Concurrency Actuation           - PEL Auto-Claim & Orphan Rescue
  - Downstream Circuit Breaker Supervisor   - Exp Backoff with Full Jitter (1.0x - 3.0x)
       │                                           │
       ▼                                           ▼
[ Explainable Decision Ledger ]           [ PostgreSQL / SQLite ACID Store ]
```

---

## 🌟 Core Technical Innovations

### 1. Autonomous Adaptive Policy Engine (Closed-Loop Feedback)
Unlike static worker pools that choke during traffic spikes or pound failing APIs during outages, EventForge continuously measures telemetry ($Q$, $L_{p95}$, $E_{429}$) and operates a 4-state finite state machine:
- **`NORMAL`**: 4 baseline workers, $0\text{ms}$ backpressure delay, $1.0\times$ retry multiplier.
- **`PRESSURE`**: Triggered when $Q \ge 50$ or $L_{p95} \ge 400\text{ms}$. Dynamically scales fleet up to **8 workers**, applies $50\text{ms}$ selective backpressure to low-tier events, and buffers telemetry records.
- **`DEGRADED`**: Triggered upon downstream 429 rate limits ($>15\%$) or circuit breaker trip. Clamps concurrency down to **2 workers**, triples retry backoff ($3.0\times$), and sheds low-priority load.
- **`RECOVERY`**: Cooldown stabilization phase. Probes downstream endpoints with gradual step-up scaling.

### 2. Multi-Tier Priority Queue & Financial Invariants
- **`CRITICAL`** (*Payment Intents, Refunds, Dispute Alerts*): **0ms delay immunity**, strictly forbidden from batching to preserve ACID transaction isolation, dedicated worker lanes.
- **`HIGH`** (*Invoices, Deployments, GitHub Push*): Minimal latency, rapid asynchronous execution.
- **`NORMAL`** (*Profile updates, Subscriptions*): Standard exponential retry handling.
- **`LOW`** (*Marketing analytics, Audit telemetry*): Dynamically throttled and packed into compressed batches during system stress.

### 3. Downstream Circuit Breaker
- **`CLOSED`**: Passes 100% of event verification calls.
- **`OPEN`**: Tripped upon 5 consecutive errors or $>50\%$ failure rate. Immediately **fails fast with zero downstream network requests**, eliminating the thundering herd problem.
- **`HALF_OPEN`**: Tests trial probes after a 5.0s cooldown before restoring full traffic.

### 4. Zero-Loss Ingestion & Idempotency Filter
- Ingestion SLA: Returns `HTTP 202 Accepted` with actual measured processing duration.
- Atomic idempotency check with composite unique constraint `(provider, event_id)` prevents duplicate processing during upstream webhook retries.
- Redis Streams Pending Entries List (PEL) auto-claim guarantees orphaned messages are recovered if a worker node crashes.
- Durable retry scheduler in PostgreSQL guarantees scheduled retries persist across process restarts.

---

## 📊 Empirical Head-to-Head Benchmark

Run with `python scripts/benchmark.py --events 200`:

| Architectural Metric | Static Baseline Pipeline | EventForge Adaptive Platform | Delta / Impact |
| :--- | :--- | :--- | :--- |
| **Worker Concurrency** | Fixed 2 Workers (Static) | Autonomous Elastic ($2 \leftrightarrow 8$ Workers) | Dynamic Fleet Scaling |
| **Priority Routing** | Flat Single Queue (FIFO) | 4-Tier Adaptive Classification | Critical Bypass |
| **Circuit Breaker** | Disabled (Thundering Herd) | Active Tripping (`CLOSED`/`OPEN`/`HALF_OPEN`) | Downstream Protection |
| **CRITICAL P95 Latency**| $14,448.41\text{ ms}$ | **$10,532.08\text{ ms}$** | **$27.1\%$ Latency Reduction** |
| **Financial Event Loss** | $23.5\%$ degraded during load | **$0.0\%$ (Zero Loss)** | **100% Guaranteed Delivery** |
| **Ingestion SLA** | $<10\text{ms}$ | **$<10\text{ms}$** | Meets Provider SLA |

---

## 🧪 10-Scenario Chaos Engineering Suite

EventForge includes a complete chaos simulation suite in `scripts/chaos_test.py`:

```bash
python scripts/chaos_test.py --scenario all
```

1. **Scenario 1**: Ingestion Traffic Spike (100 rapid events $\to$ fleet scales to 8 workers in `PRESSURE` mode).
2. **Scenario 2**: Downstream 429 Rate Limit Storm ($\to$ mode switches to `DEGRADED`, workers clamp to 2).
3. **Scenario 3**: Downstream 500 Crash Storm ($\to$ exponential backoff with full jitter scheduled).
4. **Scenario 4**: Downstream Latency Spike ($1200\text{ms} \to$ P95/P99 latency tracking).
5. **Scenario 5**: Worker Crash Simulation ($\to$ Worker 1 killed, PEL claims orphaned messages upon restart).
6. **Scenario 6**: Idempotency 20x Duplicate Flood ($\to$ exactly 1 accepted, 19 flagged duplicate).
7. **Scenario 7**: Circuit Breaker Trip & Cooldown ($\to$ trips `OPEN`, fails fast, resets to `CLOSED`).
8. **Scenario 8**: Priority Backlog Differentiation ($\to$ critical events bypass low-tier backpressure).
9. **Scenario 9**: DLQ Poison Pill Isolation ($\to$ non-retryable 400 schema error quarantined).
10. **Scenario 10**: Gradual System Recovery ($\to$ telemetry stabilization and fleet normalization).

---

## 🎨 Swiss International Dashboard Interface

The web interface is built following strict **Swiss International (International Typographic Style)** design principles:
- Pure Black, White, and Neutral Gray palette with Swiss Red (`#FF3000`) accents.
- Mathematical precision grid layout with 2px/4px solid borders and `rounded-none` geometry.
- Live WebSocket telemetry updates (`ws://127.0.0.1:8000/ws/monitor`).
- Interactive Chaos Control and Manual Policy Override testbenches.

---

## 🚀 Quickstart Guide

### Prerequisites
- Python 3.12+
- Node.js 18+ and npm
- (Optional) Docker and Docker Compose

### Option A: Local Development

#### 1. Start the Backend API & Adaptive Engine
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### 2. Start the Frontend Dashboard
```bash
cd frontend
npm install
npm run dev
```
Open [http://127.0.0.1:5173/](http://127.0.0.1:5173/) in your browser.

### Option B: Full Docker Stack (PostgreSQL + Redis + Backend + Frontend)
```bash
docker compose up --build
```
- **Frontend Dashboard**: [http://localhost:3000/](http://localhost:3000/)
- **Backend API & Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Live WebSocket Monitor**: `ws://localhost:8000/ws/monitor`

### 3. Run Automated Tests
```bash
python -m pytest backend/tests -v
```
*Executes 33 comprehensive test cases covering HMAC verification, concurrent idempotency bursts, durable retries, worker crash recovery, DLQ quarantine, adaptive transitions, and circuit breaking.*

### 4. Run Benchmark Suite
```bash
python scripts/benchmark.py --events 200
```


---

## 📚 Technical Documentation

- [System Design & Architecture Spec](docs/system-design.md)
- [Adaptive Policy Engine & Mathematical Models](docs/adaptive-policy.md)
- [Empirical Benchmarking Analysis](docs/benchmarking.md)
- [Staff Distributed Systems Interview Guide](docs/interview-notes.md)

---

## 📄 License
MIT License. Created for the EventForge Reliability & Systems Portfolio.
