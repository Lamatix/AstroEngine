"""
n8n entegrasyon servisi.
- n8n workflow tetikleme (retry/backoff ile)
- FastAPI'ye write-back (job sonucu güncelleme)
- 500 hatalarında sistemi çökertme, log at
"""
import logging
from typing import Dict, Any, Optional

import httpx
from tenacity import (
    retry, wait_exponential, stop_after_attempt,
    retry_if_exception_type, before_sleep_log, RetryError
)

from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger("n8n_service")


class N8NServiceError(Exception):
    pass


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(httpx.HTTPStatusError),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=False,
)
async def _post_with_retry(target_url: str, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(target_url, json=payload, headers=headers)
            if response.status_code >= 500:
                logger.error("n8n 5xx hatası (status=%d): %s", response.status_code, response.text)
                response.raise_for_status()  # retry için exception fırlat
            elif response.status_code >= 400:
                logger.warning("n8n 4xx hatası (status=%d): %s", response.status_code, response.text)
                return {"status": "client_error", "code": response.status_code, "body": response.text}

            logger.info("n8n workflow başarıyla tetiklendi, status=%d", response.status_code)
            try:
                return response.json()
            except Exception:
                return {"status": "ok", "raw": response.text}
    except httpx.HTTPStatusError:
        raise  # tenacity yeniden dener
    except httpx.RequestError as exc:
        logger.error("n8n bağlantı hatası: %s", exc)
        return {"status": "connection_error", "error": str(exc)}
    except Exception as exc:
        logger.exception("n8n beklenmeyen hata: %s", exc)
        return {"status": "error", "error": str(exc)}


async def trigger_n8n_workflow(
    payload: Dict[str, Any],
    workflow_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    n8n webhook'unu async olarak tetikler.
    3 deneme sonunda başarısız olursa hata logu bırakır, sistemi çökertmez.
    """
    n8n_url = getattr(settings, "N8N_WEBHOOK_URL", "")
    api_key = getattr(settings, "N8N_API_KEY", "")

    if not n8n_url:
        logger.warning("N8N_WEBHOOK_URL yapılandırılmamış, n8n tetikleme atlanıyor.")
        return {"status": "skipped", "reason": "N8N_WEBHOOK_URL not configured"}

    target_url = f"{n8n_url}/{workflow_path}" if workflow_path else n8n_url
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-N8N-API-KEY"] = api_key

    try:
        return await _post_with_retry(target_url, payload, headers)
    except RetryError as exc:
        # reraise=False -> tüm denemeler tükendiğinde RetryError; sistemi çökertme
        logger.error("n8n 3 denemede başarısız (5xx): %s", exc)
        return {"status": "failed", "error": "n8n 5xx - tüm denemeler tükendi"}


async def write_back_job_result(
    job_id: str,
    result: Dict[str, Any],
    success: bool = True,
) -> Dict[str, Any]:
    """n8n iş akışına iş sonucunu geri bildirir (write-back)."""
    write_back_payload = {"job_id": job_id, "success": success, "result": result}
    logger.info("n8n write-back gönderiliyor: job_id=%s, success=%s", job_id, success)
    return await trigger_n8n_workflow(write_back_payload, workflow_path="callback")
