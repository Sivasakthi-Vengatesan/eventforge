from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.app.database.connection import get_db
from backend.app.schemas.metrics import SystemMetricsSummary, HealthCheckResponse
from backend.app.monitoring.metrics_collector import metrics_collector
from backend.app.queue.redis_client import get_redis_client
from backend.app.workers.manager import worker_manager

router = APIRouter(tags=["Metrics & Health"])

@router.get("/metrics", response_model=SystemMetricsSummary, summary="Get real-time aggregated metrics")
async def get_system_metrics():
    metrics = await metrics_collector.get_system_metrics()
    return SystemMetricsSummary(**metrics)

@router.get("/health", response_model=HealthCheckResponse, summary="System health check")
async def health_check(db: AsyncSession = Depends(get_db)):
    db_status = "HEALTHY"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"UNHEALTHY ({str(e)})"

    redis_status = "HEALTHY"
    try:
        client, is_embedded = await get_redis_client()
        redis_status = "HEALTHY (EMBEDDED)" if is_embedded else "HEALTHY (CONNECTED)"
    except Exception as e:
        redis_status = f"UNHEALTHY ({str(e)})"

    active_w = len(worker_manager.get_active_worker_ids())
    workers_status = f"{active_w} ACTIVE" if active_w > 0 else "NO_WORKERS"

    overall = "HEALTHY" if "HEALTHY" in db_status and "HEALTHY" in redis_status else "DEGRADED"

    return HealthCheckResponse(
        status=overall,
        database=db_status,
        redis=redis_status,
        workers=workers_status,
        timestamp=datetime.now(timezone.utc)
    )

@router.get("/health/redis", summary="Redis health endpoint")
async def redis_health():
    try:
        client, is_embedded = await get_redis_client()
        if not is_embedded:
            await client.ping()
            return {
                "status": "HEALTHY",
                "mode": "REDIS_SERVER",
                "connected": True,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            return {
                "status": "HEALTHY (EMBEDDED)",
                "mode": "EMBEDDED_STREAM_ENGINE",
                "connected": False,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    except Exception as e:
        return {
            "status": "UNHEALTHY",
            "mode": "UNAVAILABLE",
            "connected": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@router.get("/health/database", summary="Database health endpoint")
async def db_health(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {
            "status": "HEALTHY",
            "connected": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            "status": "UNHEALTHY",
            "connected": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.get("/system/stats", summary="Comprehensive system telemetry")
async def system_stats():
    metrics = await metrics_collector.get_system_metrics()
    return {
        "metrics": metrics,
        "active_workers": worker_manager.get_active_worker_ids()
    }
