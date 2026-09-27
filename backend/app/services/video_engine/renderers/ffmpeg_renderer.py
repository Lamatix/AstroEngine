"""
FFmpeg-based renderer stub. Intended for local/self-hosted rendering pipelines
that compose stock footage / generated frames + audio into a final MP4 using
ffmpeg, respecting the target resolution and safe zones supplied in format_spec.

Requires the `ffmpeg` binary to be available on PATH in the deployment image.
"""
import asyncio
import os
import uuid

from app.config.settings import get_settings
from app.services.video_engine.renderers.base import BaseRenderer, RenderResult

settings = get_settings()


class FFmpegRenderer(BaseRenderer):
    backend_name = "ffmpeg"

    async def render(self, job_id: uuid.UUID, prompt: str, format_spec: dict) -> RenderResult:
        os.makedirs(settings.VIDEO_STORAGE_PATH, exist_ok=True)
        output_path = os.path.join(settings.VIDEO_STORAGE_PATH, f"{job_id}.mp4")
        width, height, fps = format_spec["width"], format_spec["height"], format_spec["fps"]

        # Placeholder pipeline: generates a solid-color test clip at the target
        # resolution/fps. Replace the filter graph with the real asset-composition
        # pipeline (frames from an image/video generation model + TTS audio track).
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c=black:s={width}x{height}:r={fps}:d=5",
            "-pix_fmt", "yuv420p",
            output_path,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"ffmpeg render failed: {stderr.decode(errors='ignore')}")

        return RenderResult(output_url=output_path, metadata={"width": width, "height": height, "fps": fps})
