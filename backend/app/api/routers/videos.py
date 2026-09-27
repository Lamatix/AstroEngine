import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.deps import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.models.video_job import VIDEO_FORMAT_SPECS, VideoFormat, VideoJob
from app.schemas.video import VideoFormatSpecRead, VideoJobCreate, VideoJobRead
from app.services.credit_service import charge_credits
from app.services.video_engine.job_manager import create_job, process_job

router = APIRouter(prefix="/videos", tags=["Video Engine"])
settings = get_settings()

_CREDIT_COST_BY_FORMAT = {
    VideoFormat.REEL_SHORT: settings.CREDIT_COST_VIDEO_SHORT,
    VideoFormat.YOUTUBE_MAIN: settings.CREDIT_COST_VIDEO_MAIN,
}


@router.get("/formats", response_model=list[VideoFormatSpecRead])
async def list_formats():
    return [{"format": key, **spec} for key, spec in VIDEO_FORMAT_SPECS.items()]


@router.post("/jobs", response_model=VideoJobRead, status_code=status.HTTP_201_CREATED)
async def create_video_job(
    payload: VideoJobCreate,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    cost = _CREDIT_COST_BY_FORMAT[payload.format]

    await charge_credits(db, user, cost, description=f"Video generation ({payload.format.value})")
    job = await create_job(db, user.id, payload.prompt, payload.format, cost)
    await db.commit()
    await db.refresh(job)

    background_tasks.add_task(process_job, job.id)
    return job


@router.get("/jobs", response_model=list[VideoJobRead])
async def list_video_jobs(
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    result = await db.execute(
        select(VideoJob).where(VideoJob.user_id == user.id).order_by(VideoJob.created_at.desc()).limit(limit)
    )
    return result.scalars().all()


@router.get("/jobs/{job_id}", response_model=VideoJobRead)
async def get_video_job(
    job_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(VideoJob).where(VideoJob.id == job_id, VideoJob.user_id == user.id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video job not found")
    return job