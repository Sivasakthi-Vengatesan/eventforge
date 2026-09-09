from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.database.connection import get_db
from backend.app.models.worker import Worker
from backend.app.schemas.metrics import WorkerSchema
from backend.app.workers.manager import worker_manager

router = APIRouter(prefix="/workers", tags=["Worker Pool Management"])

@router.get("", response_model=List[WorkerSchema], summary="List all worker states and metrics")
async def list_workers(db: AsyncSession = Depends(get_db)):
    stmt = select(Worker).order_by(Worker.id.asc())
    res = await db.execute(stmt)
    workers = res.scalars().all()
    return [WorkerSchema.model_validate(w) for w in workers]

@router.post("/{worker_id}/restart", summary="Restart or scale up worker")
async def restart_worker(worker_id: str):
    await worker_manager.restart_worker(worker_id)
    return {"status": "SUCCESS", "message": f"Worker {worker_id} restarted successfully"}

@router.post("/{worker_id}/kill", summary="Simulate worker crash")
async def kill_worker(worker_id: str):
    await worker_manager.kill_worker(worker_id)
    return {"status": "CRASHED", "message": f"Simulated crash for {worker_id}"}
