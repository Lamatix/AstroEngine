"""
Celery görev tanımları.
- generate_llm_reading: LLM çağrısı, hata durumunda retry
- render_video_job: Video render işlemi (job_manager.process_job)
"""
import asyncio
import logging
import uuid
from typing import Dict, Any, Optional

from app.workers.celery_app import celery_app

logger = logging.getLogger("celery.tasks")


def _run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, name="app.workers.tasks.generate_llm_reading",
                 max_retries=3, default_retry_delay=60, queue="llm")
def generate_llm_reading(self, prompt: str, system_prompt: Optional[str] = None,
                         provider: str = "openai") -> Dict[str, Any]:
    """LLM çağrısını Celery kuyruğunda çalıştırır; hata olursa 60 sn sonra max 3 kez tekrar dener."""
    from app.services.llm_service import llm_router

    try:
        logger.info("LLM görev başladı: provider=%s, task_id=%s", provider, self.request.id)
        result = _run_async(llm_router.generate(
            prompt=prompt, system_prompt=system_prompt, preferred_provider=provider))
        logger.info("LLM görev tamamlandı: task_id=%s, tokens=%s", self.request.id, result.tokens_used)
        return {"status": "completed", "provider": result.provider, "model": result.model,
                "output": result.output, "tokens_used": result.tokens_used}
    except Exception as exc:
        logger.error("LLM görev hatası: task_id=%s, error=%s", self.request.id, exc)
        if self.request.retries >= self.max_retries:
            logger.critical("LLM görev tüm denemeler tükendi: task_id=%s", self.request.id)
            return {"status": "failed", "error": str(exc)}
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, name="app.workers.tasks.render_video_job",
                 max_retries=2, default_retry_delay=120, queue="video", time_limit=3600)
def render_video_job(self, job_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Video render işlemini Celery kuyruğunda çalıştırır.
    job_params: {"job_id": "<uuid>"} — mevcut job_manager.process_job'u çağırır.
    """
    from app.services.video_engine.job_manager import process_job

    try:
        job_id = uuid.UUID(str(job_params["job_id"]))
        logger.info("Video render görevi başladı: job_id=%s task_id=%s", job_id, self.request.id)
        _run_async(process_job(job_id))
        logger.info("Video render tamamlandı: task_id=%s", self.request.id)
        return {"status": "completed", "job_id": str(job_id)}
    except Exception as exc:
        logger.error("Video render hatası: task_id=%s, error=%s", self.request.id, exc)
        if self.request.retries >= self.max_retries:
            logger.critical("Video render tüm denemeler tükendi: task_id=%s", self.request.id)
            return {"status": "failed", "error": str(exc)}
        raise self.retry(exc=exc, countdown=120)
