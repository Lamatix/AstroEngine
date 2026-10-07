"""
Mock renderer used for local development and tests - simulates a rendering
delay and produces a deterministic placeholder output URL without needing
GPU/video infrastructure. Now physically writes a placeholder file to disk.
"""
import asyncio
import pathlib
import uuid

from app.services.video_engine.renderers.base import BaseRenderer, RenderResult


class MockRenderer(BaseRenderer):
    backend_name = "mock"

    async def render(self, job_id: uuid.UUID, prompt: str, format_spec: dict) -> RenderResult:
        await asyncio.sleep(1)

        # Proje kök dizinindeki storage/videos klasörüne fiziksel olarak placeholder dosya yazıyoruz
        base_dir = pathlib.Path(__file__).resolve().parent.parent.parent.parent
        videos_dir = base_dir / "storage" / "videos"
        videos_dir.mkdir(parents=True, exist_ok=True)

        file_path = videos_dir / f"{job_id}.mp4"
        
        # Eğer fiziksel dosya yoksa diskte hemen oluşturuyoruz
        if not file_path.exists():
            file_path.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 100)

        output_url = f"/storage/videos/{job_id}.mp4"
        return RenderResult(
            output_url=output_url,
            metadata={
                "note": "Rendered by MockRenderer (physically written placeholder file)",
                "width": format_spec["width"],
                "height": format_spec["height"],
            },
        )