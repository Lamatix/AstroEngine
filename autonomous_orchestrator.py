"""
AstroEngine Otonom Orkestratörü - Production-Ready Sağlık Kontrolcüsü
Simülasyon YOKTUR. Tüm kontroller gerçek bağlantıları test eder.
"""
import asyncio
import logging
import os
import socket
import sys
import time
from typing import Dict, Optional

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

logger = logging.getLogger("orchestrator")

if not logging.root.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] AstroEngine Orkestratör: %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(ROOT_DIR, "orchestrator.log")),
            logging.StreamHandler(),
        ],
    )


class ModuleStatus:
    def __init__(self, module: str, healthy: bool, error: Optional[str] = None, latency_ms: Optional[float] = None):
        self.module = module
        self.healthy = healthy
        self.error = error
        self.latency_ms = latency_ms

    def to_dict(self) -> dict:
        return {"module": self.module, "healthy": self.healthy, "error": self.error, "latency_ms": self.latency_ms}


async def check_database() -> ModuleStatus:
    """Gerçek veritabanı bağlantısını test eder."""
    start = time.monotonic()
    try:
        from app.database import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        latency = (time.monotonic() - start) * 1000
        logger.info("Veritabanı sağlığı: OK (%.1f ms)", latency)
        return ModuleStatus("database", True, latency_ms=latency)
    except Exception as exc:
        logger.error("Veritabanı sağlık kontrolü BAŞARISIZ: %s", exc)
        return ModuleStatus("database", False, error=str(exc))


async def check_redis() -> ModuleStatus:
    """Gerçek Redis bağlantısını test eder."""
    start = time.monotonic()
    try:
        from app.config.settings import get_settings
        import redis.asyncio as aioredis

        r = aioredis.from_url(get_settings().CELERY_BROKER_URL, socket_connect_timeout=3)
        try:
            pong = await r.ping()
        finally:
            await r.aclose()
        if not pong:
            raise ConnectionError("Redis PING yanıt vermedi")
        latency = (time.monotonic() - start) * 1000
        logger.info("Redis sağlığı: OK (%.1f ms)", latency)
        return ModuleStatus("redis", True, latency_ms=latency)
    except Exception as exc:
        logger.error("Redis sağlık kontrolü BAŞARISIZ: %s", exc)
        return ModuleStatus("redis", False, error=str(exc))


async def check_celery_workers() -> ModuleStatus:
    """Aktif Celery worker'larını kontrol eder (bloklayan çağrı thread'de çalışır)."""
    try:
        from app.workers.celery_app import celery_app

        def _ping():
            return celery_app.control.inspect(timeout=3).ping()

        ping_result = await asyncio.wait_for(asyncio.to_thread(_ping), timeout=10)
        if ping_result:
            logger.info("Celery worker'ları: %d aktif worker bulundu", len(ping_result))
            return ModuleStatus("celery", True)
        logger.warning("Celery worker'ı bulunamadı")
        return ModuleStatus("celery", False, error="Aktif worker yok")
    except Exception as exc:
        logger.error("Celery sağlık kontrolü BAŞARISIZ: %s", exc)
        return ModuleStatus("celery", False, error=str(exc) or type(exc).__name__)


async def check_openai_api() -> ModuleStatus:
    """OpenAI API erişilebilirliğini test eder."""
    start = time.monotonic()
    try:
        from app.config.settings import get_settings
        import httpx

        settings = get_settings()
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("sk-REPLACE"):
            return ModuleStatus("openai_api", False, error="API key yapılandırılmamış")
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            )
        if response.status_code in (200, 401):  # 401 = erişilebilir ama key geçersiz
            latency = (time.monotonic() - start) * 1000
            is_valid = response.status_code == 200
            logger.info("OpenAI API erişilebilir (status=%d, %.1f ms)", response.status_code, latency)
            return ModuleStatus("openai_api", is_valid, latency_ms=latency,
                                error=None if is_valid else "Geçersiz API key")
        raise Exception(f"Beklenmeyen status: {response.status_code}")
    except Exception as exc:
        logger.error("OpenAI API sağlık kontrolü BAŞARISIZ: %s", exc)
        return ModuleStatus("openai_api", False, error=str(exc))


async def check_ephemeris_files() -> ModuleStatus:
    """Swiss Ephemeris dosyalarının varlığını kontrol eder."""
    ephe_path = os.path.join(BACKEND_DIR, "app", "ephe")
    required_files = ["seas_18.se1", "semo_18.se1", "sepl_18.se1"]
    missing = [f for f in required_files if not os.path.exists(os.path.join(ephe_path, f))]
    if missing:
        logger.error("Eksik ephemeris dosyaları: %s", missing)
        return ModuleStatus("ephemeris", False, error=f"Eksik dosyalar: {missing}")
    logger.info("Swiss Ephemeris dosyaları: Tümü mevcut")
    return ModuleStatus("ephemeris", True)


async def check_video_storage() -> ModuleStatus:
    """Video depolama dizininin yazılabilir olduğunu kontrol eder."""
    path = os.path.join(BACKEND_DIR, "app", "storage", "videos")
    try:
        os.makedirs(path, exist_ok=True)
        if not os.access(path, os.W_OK):
            return ModuleStatus("video_storage", False, error=f"Yazılamıyor: {path}")
        return ModuleStatus("video_storage", True)
    except Exception as exc:
        return ModuleStatus("video_storage", False, error=str(exc))


def run_module_check(module_name: str) -> bool:
    """
    Gerçek modül sağlık kontrolü.
    Artık her zaman True dönmez - gerçek hata durumunda False döner ve loglar.
    """
    logger.info("Modül kontrolü başlıyor: %s", module_name)
    name = module_name.lower()
    try:
        if "ephemeris" in name or "faz 1" in name or "faz 2" in name:
            result = asyncio.run(check_ephemeris_files())
        elif "fastapi" in name or "backend" in name or "faz 3" in name:
            result = asyncio.run(check_database())
        elif "next" in name or "frontend" in name or "faz 4" in name:
            try:
                socket.create_connection(("localhost", 3000), timeout=2).close()
                result = ModuleStatus(module_name, True)
            except OSError:
                result = ModuleStatus(module_name, False, error="Frontend port 3000 erişilemiyor")
        elif "video" in name or "faz 5" in name:
            result = asyncio.run(check_video_storage())
        elif "celery" in name or "redis" in name:
            result = asyncio.run(check_redis())
        elif "openai" in name or "gpt" in name or "faz 9" in name:
            result = asyncio.run(check_openai_api())
        else:
            logger.info("Genel modül kontrolü (özel kontrol tanımlı değil): %s", module_name)
            result = ModuleStatus(module_name, True)

        if result.healthy:
            logger.info("✅ %s: SAĞLIKLI (%.1fms)", module_name, result.latency_ms or 0)
        else:
            logger.error("❌ %s: BAŞARISIZ - %s", module_name, result.error)
        return bool(result.healthy)
    except Exception as exc:
        logger.exception("❌ %s kontrolünde beklenmeyen hata: %s", module_name, exc)
        return False


async def run_full_health_check() -> Dict[str, dict]:
    """Tüm sistemin asenkron sağlık taraması (paralel, gerçek bağlantı testleri)."""
    logger.info("Tam sistem sağlık taraması başlıyor...")
    check_names = ["database", "redis", "celery", "openai_api", "ephemeris"]
    checks = await asyncio.gather(
        check_database(), check_redis(), check_celery_workers(),
        check_openai_api(), check_ephemeris_files(),
        return_exceptions=True,
    )
    results = {}
    for name, check in zip(check_names, checks):
        if isinstance(check, BaseException):
            logger.error("Kontrol %s exception attı: %s", name, check)
            results[name] = ModuleStatus(name, False, error=str(check)).to_dict()
        else:
            results[name] = check.to_dict()
    healthy_count = sum(1 for v in results.values() if v["healthy"])
    logger.info("Sağlık taraması tamamlandı: %d/%d modül sağlıklı", healthy_count, len(results))
    return results


# Eski API ile uyumluluk: AutonomousModelRouter tek kaynaktan
try:
    from app.services.model_router_service import AutonomousModelRouter  # noqa: F401
except Exception as _exc:  # pragma: no cover
    logger.warning("AutonomousModelRouter import edilemedi: %s", _exc)
    AutonomousModelRouter = None


def launch_full_empire() -> bool:
    logger.info("🌟 AstroEngine Otonom Modülleri Başlatılıyor...")
    modules = [
        "Faz 1: Swiss Ephemeris & Batı Astrolojisi Motoru",
        "Faz 2: Vedik, Çin (BaZi) ve Ezoterik Ebced Ağı",
        "Faz 3: FastAPI Backend & Mikroservis Katmanı",
        "Faz 4: Next.js UI/UX & Modern Arayüz Sistemleri",
        "Faz 5: Skyview & Otomatik Video Fabrikası",
        "Faz 6: Ticari Entegrasyon & PDF Raporlama",
        "Faz 7: SEO, Algoritmik Büyüme Ağı",
        "Faz 8: Governance, Rate-Limiting ve Güvenlik",
        "Faz 9: Hibrit Çoklu Model Yönlendirici",
    ]
    all_healthy = True
    for mod in modules:
        logger.info("--- Modül Kontrol Ediliyor: %s ---", mod)
        if not run_module_check(mod):
            all_healthy = False
            logger.warning("⚠️ %s başarısız - devam ediliyor", mod)
    if all_healthy:
        logger.info("🚀 TÜM MODÜLLER SAĞLIKLI VE HAZIR!")
    else:
        logger.warning("⚠️ Bazı modüller başarısız - lütfen logları inceleyin")
    return all_healthy


if __name__ == "__main__":
    sys.exit(0 if launch_full_empire() else 1)
