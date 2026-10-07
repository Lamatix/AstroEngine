"""
Celery uygulama fabrikası.
Broker: Redis (CELERY_BROKER_URL)
Backend: Redis (CELERY_RESULT_BACKEND)
"""
from celery import Celery
from app.config.settings import get_settings

settings = get_settings()

celery_app = Celery(
    "astroengine",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.workers.tasks.generate_llm_reading": {"queue": "llm"},
        "app.workers.tasks.render_video_job": {"queue": "video"},
    },
)
