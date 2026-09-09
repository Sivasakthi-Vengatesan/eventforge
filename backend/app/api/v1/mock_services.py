import asyncio
import random
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from backend.app.core.config import settings
from backend.app.core.logging import logger

router = APIRouter(prefix="/mock", tags=["Mock Third-Party APIs"])

class MockConfig(BaseModel):
    success_rate: float = settings.MOCK_SUCCESS_RATE
    timeout_rate: float = settings.MOCK_TIMEOUT_RATE
    server_error_rate: float = settings.MOCK_SERVER_ERROR_RATE
    forced_behavior: Optional[str] = None # 'success', '500', '429', 'timeout', 'invalid_data'

mock_state = MockConfig()

@router.get("/config")
async def get_mock_config():
    return mock_state

@router.post("/config")
async def update_mock_config(config: MockConfig):
    global mock_state
    mock_state = config
    logger.info("Updated mock service fault injection parameters", extra={"mock_config": mock_state.model_dump()})
    return {"status": "UPDATED", "config": mock_state}

async def simulate_mock_response(provider_name: str, request: Request, payload: Dict[str, Any]):
    # Header override takes highest priority for targeted tests
    header_fault = request.headers.get("x-mock-fault") or payload.get("force_fault")
    behavior = header_fault or mock_state.forced_behavior
    
    # Intrinsic latency simulation (20ms - 80ms)
    await asyncio.sleep(random.uniform(0.02, 0.08))
    
    if behavior == "timeout":
        await asyncio.sleep(2.0)
        raise HTTPException(status_code=504, detail=f"{provider_name} Gateway Timeout: upstream connection aborted")
        
    if behavior in ["500", "error"]:
        raise HTTPException(status_code=500, detail=f"{provider_name} Internal Server Error: Database deadlock detected")
        
    if behavior == "429":
        raise HTTPException(status_code=429, detail=f"{provider_name} Rate Limit Exceeded: Retry after 2 seconds")
        
    if behavior in ["400", "invalid_data"]:
        raise HTTPException(status_code=400, detail=f"{provider_name} Bad Request: Non-retryable invalid schema in webhook body")

    # Probabilistic fault simulation if no forced behavior
    r = random.random()
    if r < mock_state.timeout_rate:
        await asyncio.sleep(1.5)
        raise HTTPException(status_code=504, detail=f"{provider_name} Gateway Timeout: connection reset by peer")
    elif r < (mock_state.timeout_rate + mock_state.server_error_rate):
        raise HTTPException(status_code=500, detail=f"{provider_name} Downstream Server Error (HTTP 500)")
        
    return {
        "status": "SUCCESS",
        "provider": provider_name,
        "processed_at": asyncio.get_event_loop().time(),
        "verification_token": f"vtok_{random.randint(100000, 999999)}"
    }

@router.post("/payment")
async def mock_payment_service(request: Request, payload: Dict[str, Any]):
    return await simulate_mock_response("MockPaymentProvider", request, payload)

@router.post("/verification")
async def mock_verification_service(request: Request, payload: Dict[str, Any]):
    return await simulate_mock_response("MockVerificationProvider", request, payload)

@router.post("/github")
async def mock_github_service(request: Request, payload: Dict[str, Any]):
    return await simulate_mock_response("MockGitHubAPI", request, payload)
