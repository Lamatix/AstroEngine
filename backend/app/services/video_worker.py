"""
Background video processing worker integrated with the credit engine.
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.video_job import VideoJob
from app.models.credit import CreditTransactionType
from app.services.credit_service import adjust_credits

logger = logging.getLogger("video_worker")


async def process_video_job(job_id: str, db: AsyncSession, credit_cost: int = 10):
    stmt = select(VideoJob).where(VideoJob.id == job_id)
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()

    if not job:
        logger.error("VideoJob %s not found for processing.", job_id)
        return

    user_uuid = job.user_id

    try:
        # İşleme başla
        job.status = "processing"
        job.progress_percent = 20
        await db.commit()

        await asyncio.sleep(4)  # Render simülasyonu
        job.progress_percent = 80
        await db.commit()

        # Simüle edilmiş bulut video URL'i
        job.output_url = f"https://storage.example.com/videos/{job_id}.mp4"
        job.status = "completed"
        job.progress_percent = 100
        await db.commit()

        logger.info("VideoJob %s completed successfully.", job_id)

    except Exception as exc:
        logger.error("VideoJob %s failed: %s", job_id, exc)
        
        job.status = "failed"
        await db.commit()

        # Hata durumunda (REFUND) krediyi bakiye ve ledger defterine iade et
        await adjust_credits(
            db=db,
            user_id=user_uuid,
            amount=credit_cost,
            tx_type=CreditTransactionType.REFUND,
            description=f"Video render hatası nedeniyle {credit_cost} kredi iade edildi. Job ID: {job_id}",
            reference_id=str(job_id),
            allow_negative=True
        )
        logger.info("Refunded %d credits to user %s due to job failure.", credit_cost, user_uuid)