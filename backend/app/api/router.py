from fastapi import APIRouter
from backend.app.api.v1.webhooks import router as webhooks_router
from backend.app.api.v1.events import router as events_router
from backend.app.api.v1.workers import router as workers_router
from backend.app.api.v1.dlq import router as dlq_router
from backend.app.api.v1.metrics import router as metrics_router
from backend.app.api.v1.policies import router as policies_router
from backend.app.api.v1.downstream import router as downstream_router
from backend.app.api.v1.mock_services import router as mock_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(webhooks_router)
api_v1_router.include_router(events_router)
api_v1_router.include_router(workers_router)
api_v1_router.include_router(dlq_router)
api_v1_router.include_router(metrics_router)
api_v1_router.include_router(policies_router)
api_v1_router.include_router(downstream_router)

