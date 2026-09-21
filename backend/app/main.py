import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.database.connection import init_db
from backend.app.queue.stream_manager import stream_manager
from backend.app.queue.redis_client import close_redis
from backend.app.workers.manager import worker_manager
from backend.app.monitoring.metrics_collector import metrics_collector
from backend.app.monitoring.websocket_manager import ws_manager
from backend.app.adaptive.policy_engine import get_policy_engine
from backend.app.api.router import api_v1_router
from backend.app.api.v1.mock_services import router as mock_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Rheos Distributed Gateway & Adaptive Engine...")
    await init_db()
    await stream_manager.init_stream()
    
    # Initialize Adaptive Policy Engine
    policy_engine = get_policy_engine()
    policy_engine.set_ws_manager(ws_manager)
    policy_engine.set_worker_manager(worker_manager)
    await policy_engine.start()

    # Start Worker Pool & Metrics Broadcast
    worker_manager.start_pool(settings.WORKER_COUNT)
    metrics_collector.start()
    
    logger.info("Rheos Adaptive Gateway is running and ready for high-throughput traffic.")
    yield
    logger.info("Shutting down Rheos Adaptive Gateway...")
    await policy_engine.stop()
    await worker_manager.stop_pool()
    metrics_collector.stop()
    await close_redis()
    logger.info("Shutdown complete.")



app = FastAPI(
    title="Rheos — High-Throughput Async Webhook Gateway",
    description=(
        "Production-grade distributed webhook ingestion, HMAC security verification, "
        "and asynchronous event processing gateway powered by Redis Streams, PostgreSQL, "
        "worker pools, exponential backoff retries, and real-time WebSocket observability."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app|https://.*\.onrender\.com|http://localhost:\d+|http://127\.0\.0\.1:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include Routers
app.include_router(api_v1_router)
app.include_router(mock_router)

# WebSocket Endpoint
@app.websocket("/ws/monitor")
async def websocket_monitoring_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        # Send initial snapshot of system telemetry
        metrics = await metrics_collector.get_system_metrics()
        await websocket.send_json({"type": "INITIAL_SNAPSHOT", "data": metrics})
        while True:
            # Keep-alive receive loop
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await ws_manager.disconnect(websocket)

@app.get("/")
async def root():
    return {
        "name": "Rheos Gateway",
        "status": "OPERATIONAL",
        "docs": "/docs",
        "api_v1": "/api/v1",
        "ws_monitor": "/ws/monitor"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
