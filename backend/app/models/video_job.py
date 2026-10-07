import enum
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class VideoFormat(str, enum.Enum):
    REEL_SHORT = "reel_short"     # 9:16, 1080x1920 - Instagram Reels / YouTube Shorts
    YOUTUBE_MAIN = "youtube_main"  # 16:9, 1920x1080 - YouTube Main


class VideoJobStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


# Format specs including resolution and safe-zone rules
VIDEO_FORMAT_SPECS: Dict[str, Dict[str, Any]] = {
    VideoFormat.REEL_SHORT.value: {
        "width": 1080,
        "height": 1920,
        "aspect_ratio": "9:16",
        "fps": 30,
        "safe_zone": {"top": 250, "bottom": 320, "left": 60, "right": 60},
        "max_duration_seconds": 90,
    },
    VideoFormat.YOUTUBE_MAIN.value: {
        "width": 1920,
        "height": 1080,
        "aspect_ratio": "16:9",
        "fps": 30,
        "safe_zone": {"top": 80, "bottom": 80, "left": 80, "right": 80},
        "max_duration_seconds": 900,
    },
}


class VideoJob(Base):
    __tablename__ = "video_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    format: Mapped[VideoFormat] = mapped_column(Enum(VideoFormat), nullable=False)
    status: Mapped[VideoJobStatus] = mapped_column(Enum(VideoJobStatus), default=VideoJobStatus.QUEUED, index=True)
    renderer_backend: Mapped[str] = mapped_column(String(50), default="mock")
    credits_charged: Mapped[int] = mapped_column(Integer, default=0)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    output_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # User İlişkisi
    user: Mapped["User"] = relationship("User", back_populates="video_jobs")