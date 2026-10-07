"""
Pluggable renderer interface for the Multi-Format Video Engine.

Any concrete renderer (mock, ffmpeg-based, or an external video-generation API)
implements `BaseRenderer.render`. Swap backends via VIDEO_RENDERER_BACKEND in .env
without touching the job-queue or API layer.
"""
import abc
import uuid


class RenderResult:
    def __init__(self, output_url: str, metadata: dict | None = None):
        self.output_url = output_url
        self.metadata = metadata or {}


class BaseRenderer(abc.ABC):
    backend_name: str

    @abc.abstractmethod
    async def render(self, job_id: uuid.UUID, prompt: str, format_spec: dict) -> RenderResult:
        """Render a video job and return the resulting output location."""
        ...
