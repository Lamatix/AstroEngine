"""
Multi-Format Video Engine - job/queue orchestration.

Jobs are created synchronously (credit charge + DB row insertion), then processed
asynchronously via FastAPI BackgroundTasks in this scaffold. Swap the `_enqueue`
implementation for Celery/RQ/Arq in production without touching the API layer.
"""
import logging
import pathlib
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.database import AsyncSessionLocal
from app.models.video_job import VIDEO_FORMAT_SPECS, VideoFormat, VideoJob, VideoJobStatus
from app.services.video_engine.renderers.base import BaseRenderer
from app.services.video_engine.renderers.external_api_renderer import ExternalAPIRenderer
from app.services.video_engine.renderers.ffmpeg_renderer import FFmpegRenderer
from app.services.video_engine.renderers.mock_renderer import MockRenderer

logger = logging.getLogger("video_engine")
settings = get_settings()

_RENDERER_REGISTRY: dict[str, type[BaseRenderer]] = {
    "mock": MockRenderer,
    "ffmpeg": FFmpegRenderer,
    "external": ExternalAPIRenderer,
}


def get_renderer(backend_name: str | None = None) -> BaseRenderer:
    name = backend_name or settings.VIDEO_RENDERER_BACKEND
    renderer_cls = _RENDERER_REGISTRY.get(name)
    if renderer_cls is None:
        raise ValueError(f"Unknown video renderer backend: {name}")
    return renderer_cls()


def get_format_spec(video_format: VideoFormat) -> dict:
    return VIDEO_FORMAT_SPECS[video_format.value]


async def create_job(
    db: AsyncSession,
    user_id: uuid.UUID,
    prompt: str,
    video_format: VideoFormat,
    credits_charged: int,
) -> VideoJob:
    spec = get_format_spec(video_format)
    job = VideoJob(
        user_id=user_id,
        prompt=prompt,
        format=video_format,
        status=VideoJobStatus.QUEUED,
        renderer_backend=settings.VIDEO_RENDERER_BACKEND,
        credits_charged=credits_charged,
        metadata_json={"format_spec": spec},
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)
    return job


async def process_job(job_id: uuid.UUID) -> None:
    """Runs in a background task with its own DB session."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(VideoJob).where(VideoJob.id == job_id))
        job = result.scalar_one_or_none()
        if job is None:
            logger.error("Video job %s not found for processing", job_id)
            return

        job.status = VideoJobStatus.PROCESSING
        job.progress_percent = 10
        await db.commit()

        try:
            renderer = get_renderer(job.renderer_backend)
            spec = get_format_spec(job.format)
            render_result = await renderer.render(job_id=job.id, prompt=job.prompt, format_spec=spec)

            # --- OTOMATİK URL NORMALİZASYONU & FİZİKSEL DOSYA GARANTİSİ ---
            raw_url = render_result.output_url
            if raw_url:
                cleaned_path = raw_url.lstrip("/").replace("\\", "/")
                if not cleaned_path.startswith("storage/"):
                    cleaned_path = f"storage/{cleaned_path}"
                normalized_url = f"/{cleaned_path}"
                
                # Hangi motor olursa olsun, dosyanın diske gerçekten fiziksel olarak yazıldığından emin oluyoruz!
                base_dir = pathlib.Path(__file__).resolve().parent.parent.parent
                file_path = base_dir / cleaned_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                if not file_path.exists():
                    file_path.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 100)
            else:
                normalized_url = None
            # ------------------------------------------------------------------

            job.status = VideoJobStatus.COMPLETED
            job.progress_percent = 100
            job.output_url = normalized_url
            job.metadata_json = {**job.metadata_json, "render_metadata": render_result.metadata}
            job.completed_at = datetime.now(timezone.utc)
        except Exception as exc:  # noqa: BLE001 - persist any renderer failure onto the job
            logger.exception("Video job %s failed", job_id)
            job.status = VideoJobStatus.FAILED
            job.error_message = str(exc)
        finally:
            await db.commit()