import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.video_job import VideoFormat, VideoJobStatus


class VideoJobCreate(BaseModel):
    prompt: str = Field(min_length=3, max_length=4000)
    format: VideoFormat


class VideoJobRead(BaseModel):
    id: uuid.UUID
    prompt: str
    format: VideoFormat
    status: VideoJobStatus
    renderer_backend: str
    credits_charged: int
    progress_percent: int
    output_url: str | None
    error_message: str | None
    metadata_json: dict
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class VideoFormatSpecRead(BaseModel):
    format: str
    width: int
    height: int
    aspect_ratio: str
    fps: int
    safe_zone: dict
    max_duration_seconds: int
