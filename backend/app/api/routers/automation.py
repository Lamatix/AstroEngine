from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging
import os
import sys

from app.services.model_router_service import model_router_instance
from app.services.n8n_service import trigger_n8n_workflow, write_back_job_result  # noqa: F401

logger = logging.getLogger("automation_router")
router = APIRouter(prefix="/automation", tags=["Automation"])


class N8NTaskRequest(BaseModel):
    task_type: str = Field(..., example="gpt_strategy")
    store_id: Optional[str] = Field("master_store", example="store_01")
    payload: Dict[str, Any] = Field(...)


class N8NCallbackRequest(BaseModel):
    job_id: str
    success: bool
    result: Dict[str, Any]
    error: Optional[str] = None


@router.post("/execute-task", summary="n8n Otonom Görev Köprüsü")
async def execute_n8n_task(request: N8NTaskRequest, background_tasks: BackgroundTasks):
    try:
        result = model_router_instance.route_task(request.task_type, request.payload)
        background_tasks.add_task(
            trigger_n8n_workflow,
            {"task_type": request.task_type, "store_id": request.store_id, "result": result},
        )
        return {"status": "success", "store_id": request.store_id, "task_type": request.task_type, "data": result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("execute_n8n_task hatası: %s", exc)
        raise HTTPException(status_code=500, detail=f"Otonom görev hatası: {str(exc)}")


@router.post("/n8n-callback", summary="n8n Write-Back - İş Sonucu Bildirimi")
async def n8n_callback(payload: N8NCallbackRequest):
    """n8n'den gelen iş tamamlanma bildirimini alır ve işler."""
    logger.info("n8n callback alındı: job_id=%s, success=%s", payload.job_id, payload.success)
    if not payload.success:
        logger.error("n8n job başarısız: job_id=%s, error=%s", payload.job_id, payload.error)
    return {"status": "received", "job_id": payload.job_id}


@router.get("/health", summary="Otomasyon servisi sağlık kontrolü")
async def automation_health():
    try:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
        if project_root not in sys.path:
            sys.path.append(project_root)
        from autonomous_orchestrator import run_full_health_check
        results = await run_full_health_check()
        return {"status": "ok", "checks": results}
    except Exception as exc:
        logger.error("Health check hatası: %s", exc)
        return {"status": "degraded", "error": str(exc)}
