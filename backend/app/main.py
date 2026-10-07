import os
import pathlib
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession

# .env dosyasındaki ortam değişkenlerini yükle
load_dotenv()

from app.database import get_db

# AstroEngine Sınıfı
from app.services.astro_engine import astro_engine

# LLM Service (Yedeklemeli ve logging destekli router)
from app.services.llm_service import llm_router

# ------------------------------------------------------------------
# API ROUTER'LARININ YÜKLENMESİ
# ------------------------------------------------------------------
from app.api.routers.auth import router as auth_router
from app.api.routers.users import router as users_router
from app.api.routers.credits import router as credits_router
from app.api.routers.videos import router as videos_router
from app.api.routers.llm import router as llm_api_router
from app.api.routers.stripe import router as stripe_router
from app.api.routers.automation import router as automation_router

app = FastAPI(
    title="AstroEngine & AI Service Platform REST API",
    description="Doğum haritası, transit, sinastri analizi, video işleme, LLM ve ödeme servisleri sunan bütünleşik API.",
    version="1.2.0"
)

# ------------------------------------------------------------------
# CORS MİDDLEWARE
# ------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# STATİK DOSYA SERVİSİ (MUTLAK YOL - APP/STORAGE GARANTİLİ)
# ------------------------------------------------------------------
BASE_DIR = pathlib.Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / "storage"
VIDEOS_DIR = STORAGE_DIR / "videos"

VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/storage", StaticFiles(directory=str(STORAGE_DIR)), name="storage")


# ------------------------------------------------------------------
# ROUTER'LARIN BİRLEŞTİRİLMESİ
# ------------------------------------------------------------------
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(credits_router, prefix="/api/v1")
app.include_router(videos_router, prefix="/api/v1")
app.include_router(llm_api_router, prefix="/api/v1")
app.include_router(stripe_router, prefix="/api/v1")
app.include_router(automation_router, prefix="/api/v1")

# ------------------------------------------------------------------
# LLM SERVİS YARDIMCISI & KİŞİSELLEŞTİRİLMİŞ PROMPT
# ------------------------------------------------------------------

class LLMProvider(str, Enum):
    NONE = "none"
    OPENAI = "openai"
    GEMINI = "gemini"

SYSTEM_PROMPT = (
    "Sen Sercan Bilir için özelleştirilmiş, profesyonel bir astrolog ve dijital içerik danışmanısın. "
    "Sercan; Instagram Reels ve YouTube mecralarında günlük/haftalık yüksek performanslı astroloji içerikleri "
    "üreten bir içerik yaratıcısıdır. "
    "Astrolojik analizleri yaparken hem derinlikli, doğru ve teknik astrolojik bilgiyi sun hem de "
    "çıktıların sosyal medya videolarında (Reels metni, YouTube senaryosu veya başlık fikirleri) "
    "doğrudan kullanılabilir, akıcı ve dikkat çekici bir tonda olmasını sağla."
)

async def generate_astrology_interpretation(
    prompt: str, 
    provider: LLMProvider,
    db: Optional[AsyncSession] = None,
    user_id: Optional[str] = None
) -> Optional[str]:
    if provider == LLMProvider.NONE:
        return None

    try:
        preferred = provider.value if provider in [LLMProvider.OPENAI, LLMProvider.GEMINI] else None
        
        result = await llm_router.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            preferred_provider=preferred,
            db=db,
            user_id=user_id
        )
        return result.output
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM Üretim Hatası: {str(e)}")

# ------------------------------------------------------------------
# PYDANTIC İSTEK & YANIT ŞEMALARI
# ------------------------------------------------------------------

class BirthDataRequest(BaseModel):
    year: int = Field(1987, example=1987, description="Doğum yılı")
    month: int = Field(7, example=7, ge=1, le=12, description="Doğum ayı (Temmuz)")
    day: int = Field(14, example=14, ge=1, le=31, description="Doğum günü")
    hour: int = Field(12, example=12, ge=0, le=23, description="Doğum saati")
    minute: int = Field(0, example=0, ge=0, le=59, description="Doğum dakikası")
    lat: float = Field(41.0082, example=41.0082, description="Enlem (İstanbul Varsayılanı)")
    lon: float = Field(28.9784, example=28.9784, description="Boylam (İstanbul Varsayılanı)")
    tz_offset: Optional[float] = Field(None, example=3.0, description="Opsiyonel sabitleme offset'i")
    timezone_str: str = Field("Europe/Istanbul", example="Europe/Istanbul", description="IANA zaman dilimi")
    house_system: str = Field("P", example="P", description="Ev sistemi (P: Placidus, K: Koch, W: Whole Sign)")

class NatalAnalysisRequest(BaseModel):
    birth_data: BirthDataRequest = Field(default_factory=BirthDataRequest)
    llm_provider: LLMProvider = Field(
        LLMProvider.NONE, 
        description="Otomatik yorum için LLM sağlayıcı seçimi ('none', 'openai', 'gemini')"
    )

class TransitRequest(BaseModel):
    birth_data: BirthDataRequest = Field(default_factory=BirthDataRequest)
    transit_date: Optional[str] = Field(
        None, 
        example="2026-09-24T12:00:00", 
        description="ISO formatında transit tarihi"
    )
    llm_provider: LLMProvider = Field(
        LLMProvider.NONE, 
        description="Otomatik yorum için LLM sağlayıcı seçimi"
    )

class SynastryRequest(BaseModel):
    person_a_name: str = Field("Sercan Bilir", example="Sercan Bilir")
    person_a_data: BirthDataRequest = Field(default_factory=BirthDataRequest)
    person_b_name: str = Field("Partner / Kişi B", example="Ayşe")
    person_b_data: BirthDataRequest = Field(default_factory=BirthDataRequest)
    llm_provider: LLMProvider = Field(
        LLMProvider.NONE, 
        description="Otomatik yorum için LLM sağlayıcı seçimi"
    )

# ------------------------------------------------------------------
# ENDPOINT'LER
# ------------------------------------------------------------------

@app.get("/", tags=["Health Check"])
def root_check():
    return {"status": "online", "service": "AstroEngine API", "version": "1.2.0"}

@app.get("/health", tags=["Health Check"])
@app.get("/api/v1/health", tags=["Health Check"])
async def health_check():
    """Gerçek orkestratör sağlık taraması (DB, Redis, Celery, OpenAI, Ephemeris)."""
    try:
        import sys as _sys
        _root = str(pathlib.Path(__file__).resolve().parents[2])
        if _root not in _sys.path:
            _sys.path.append(_root)
        from autonomous_orchestrator import run_full_health_check
        checks = await run_full_health_check()
        all_ok = all(c.get("healthy") for c in checks.values())
        return {"status": "ok" if all_ok else "degraded", "service": "AstroEngine Core", "checks": checks}
    except Exception as exc:
        return {"status": "degraded", "service": "AstroEngine Core", "error": str(exc)}

@app.post("/api/v1/natal-chart", summary="Doğum Haritası Verilerini Hesapla", tags=["Astrology"])
def get_natal_chart(data: BirthDataRequest):
    try:
        chart_data = astro_engine.calculate_natal_chart(**data.model_dump())
        return {"success": True, "data": chart_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hesaplama hatası: {str(e)}")

@app.post("/api/v1/natal-analysis", summary="Doğum Haritası Analizi ve İsteğe Bağlı LLM Yorumu", tags=["Astrology"])
async def analyze_natal_chart(req: NatalAnalysisRequest, db: AsyncSession = Depends(get_db)):
    try:
        chart_data = astro_engine.calculate_natal_chart(**req.birth_data.model_dump())
        prompt = astro_engine.build_astrology_prompt(req.birth_data.model_dump())
        
        interpretation = await generate_astrology_interpretation(prompt, req.llm_provider, db=db)

        return {
            "success": True,
            "data": chart_data,
            "prompt": prompt,
            "interpretation": interpretation
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Natal analiz hatası: {str(e)}")

@app.post("/api/v1/transits", summary="Transit ve Öngörü Analizi", tags=["Astrology"])
async def get_transits(req: TransitRequest, db: AsyncSession = Depends(get_db)):
    try:
        t_dt = datetime.fromisoformat(req.transit_date) if req.transit_date else datetime.now()

        transit_data = astro_engine.calculate_transits(req.birth_data.model_dump(), transit_dt=t_dt)
        prompt = astro_engine.build_transit_prompt(req.birth_data.model_dump(), transit_dt=t_dt)
        
        interpretation = await generate_astrology_interpretation(prompt, req.llm_provider, db=db)

        return {
            "success": True, 
            "data": transit_data,
            "llm_prompt": prompt,
            "interpretation": interpretation
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transit hesaplama hatası: {str(e)}")

@app.post("/api/v1/synastry", summary="Sinastri (İlişki Uyumu) Analizi", tags=["Astrology"])
async def get_synastry(req: SynastryRequest, db: AsyncSession = Depends(get_db)):
    try:
        synastry_data = astro_engine.calculate_synastry(
            req.person_a_data.model_dump(), 
            req.person_b_data.model_dump()
        )
        prompt = astro_engine.build_synastry_prompt(
            req.person_a_data.model_dump(),
            req.person_b_data.model_dump(),
            name_a=req.person_a_name,
            name_b=req.person_b_name
        )

        interpretation = await generate_astrology_interpretation(prompt, req.llm_provider, db=db)

        return {
            "success": True,
            "data": synastry_data,
            "llm_prompt": prompt,
            "interpretation": interpretation
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sinastri hesaplama hatası: {str(e)}")

# ------------------------------------------------------------------
# UVICORN İLE BAŞLATMA
# ------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)