"""
Renderer stub that delegates to an external video-generation API/provider
(e.g. a third-party text-to-video service). Configure its base URL/API key via
environment variables and wire the request/response shape below to the
provider's actual contract before enabling this backend in production.
"""
import uuid

import httpx

from app.config.settings import get_settings
from app.services.video_engine.renderers.base import BaseRenderer, RenderResult

settings = get_settings()


class ExternalAPIRenderer(BaseRenderer):
    backend_name = "external"

    async def render(self, job_id: uuid.UUID, prompt: str, format_spec: dict) -> RenderResult:
        # Example shape only - replace endpoint/payload/parsing with the real
        # provider's API contract once credentials are available.
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                "https://api.example-video-provider.com/v1/generate",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={
                    "prompt": prompt,
                    "width": format_spec["width"],
                    "height": format_spec["height"],
                    "fps": format_spec["fps"],
                    "max_duration_seconds": format_spec["max_duration_seconds"],
                },
            )
            response.raise_for_status()
            data = response.json()
            return RenderResult(output_url=data["output_url"], metadata=data.get("metadata", {}))
