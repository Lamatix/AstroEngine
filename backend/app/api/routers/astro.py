import logging
from datetime import datetime
from enum import Enum
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user
from app.database import get_db
from app.models.user import SavedChart, User
from app.services.astro_engine import astro_engine
from app.services.llm_service import llm_router

logger = logging.getLogger("app")

router = APIRouter(prefix="/astro", tags=["Astro Engine"])


# ------------------------------------------------------------------
# LLM PROVIDER & SYSTEM PROMPT
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
    """LLM Router üzerinden asenkron ve yedeklemeli (fallback) olarak yorum metni üretir."""
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
# SCHEMAS (Pydantic Modelleri)
# ------------------------------------------------------------------

class BirthDataSchema(BaseModel):
    year: int = Field(1987, example=1987)
    month: int = Field(7, example=7, ge=1, le=12)
    day: int = Field(14, example=14, ge=1, le=31)
    hour: int = Field(12, example=12, ge=0, le=23)
    minute: int = Field(30, example=30, ge=0, le=59)
    lat: float = Field(41.0082, example=41.0082)
    lon: float = Field(28.9784, example=28.9784)
    tz_offset: Optional[float] = Field(3.0, example=3.0)
    timezone_str: str = Field("Europe/Istanbul", example="Europe/Istanbul")
    house_system: str = Field("P", example="P")


class SaveChartRequest(BaseModel):
    title: str = Field("Sercan Bilir Doğum Haritası", example="Sercan Bilir Doğum Haritası")
    birth_data: BirthDataSchema


class SavedChartResponse(BaseModel):
    id: int
    title: str
    year: int
    month: int
    day: int
    hour: int
    minute: int
    lat: float
    lon: float
    timezone_str: str
    created_at: datetime

    class Config:
        from_attributes = True


class NatalAnalysisRequest(BaseModel):
    birth_data: BirthDataSchema = Field(default_factory=BirthDataSchema)
    llm_provider: LLMProvider = Field(LLMProvider.NONE, description="Otomatik yorum için LLM sağlayıcı seçimi")


class TransitRequest(BaseModel):
    birth_data: BirthDataSchema = Field(default_factory=BirthDataSchema)
    transit_date: Optional[str] = Field(None, example="2026-09-24T12:00:00", description="ISO formatında transit tarihi")
    llm_provider: LLMProvider = Field(LLMProvider.NONE, description="Otomatik yorum için LLM sağlayıcı seçimi")


class SynastryRequest(BaseModel):
    person_a_name: str = Field("Sercan Bilir", example="Sercan Bilir")
    person_a_data: BirthDataSchema = Field(default_factory=BirthDataSchema)
    person_b_name: str = Field("Partner / Kişi B", example="Ayşe")
    person_b_data: BirthDataSchema = Field(default_factory=BirthDataSchema)
    llm_provider: LLMProvider = Field(LLMProvider.NONE, description="Otomatik yorum için LLM sağlayıcı seçimi")


# ------------------------------------------------------------------
# ENDPOINTS
# ------------------------------------------------------------------

@router.post("/prompt", summary="Astroloji Prompt'u Üret")
async def generate_prompt(
    birth_data: dict = Body(
        ...,
        openapi_examples={
            "default": {
                "summary": "Örnek Doğum Verisi",
                "value": {
                    "year": 1987,
                    "month": 7,
                    "day": 14,
                    "hour": 12,
                    "minute": 30,
                    "lat": 41.0082,
                    "lon": 28.9784,
                    "tz_offset": 3.0,
                },
            }
        },
    )
):
    """
    Doğum verilerini alarak AstroEngine üzerinden LLM için ham astroloji prompt'u üretir.
    """
    try:
        prompt = astro_engine.build_astrology_prompt(birth_data)
        return {"status": "success", "prompt": prompt}
    except Exception as e:
        logger.exception("Astro engine hesaplama hatası:")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/natal-chart", summary="Doğum Haritası Verilerini Hesapla")
def get_natal_chart(data: BirthDataSchema):
    """
    Doğum verilerini kullanarak astro_engine ile teknik doğum haritası verilerini hesaplar.
    """
    try:
        chart_data = astro_engine.calculate_natal_chart(**data.model_dump())
        return {"success": True, "data": chart_data}
    except Exception as e:
        logger.exception("Doğum haritası hesaplama hatası:")
        raise HTTPException(status_code=500, detail=f"Hesaplama hatası: {str(e)}")


@router.post("/natal-analysis", summary="Doğum Haritası Analizi ve İsteğe Bağlı LLM Yorumu")
async def analyze_natal_chart(req: NatalAnalysisRequest, db: AsyncSession = Depends(get_db)):
    """
    Doğum haritası hesaplamasını yapar ve istenirse LLM aracılığıyla özelleştirilmiş yorum üretir.
    """
    try:
        birth_dict = req.birth_data.model_dump()
        chart_data = astro_engine.calculate_natal_chart(**birth_dict)
        prompt = astro_engine.build_astrology_prompt(birth_dict)
        
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
        logger.exception("Natal analiz hatası:")
        raise HTTPException(status_code=500, detail=f"Natal analiz hatası: {str(e)}")


@router.post("/transits", summary="Transit ve Öngörü Analizi")
async def get_transits(req: TransitRequest, db: AsyncSession = Depends(get_db)):
    """
    Belirli bir tarih için transit hesaplamalarını yapar ve LLM desteğiyle yorumlar.
    """
    try:
        t_dt = datetime.fromisoformat(req.transit_date) if req.transit_date else datetime.now()
        birth_dict = req.birth_data.model_dump()

        transit_data = astro_engine.calculate_transits(birth_dict, transit_dt=t_dt)
        prompt = astro_engine.build_transit_prompt(birth_dict, transit_dt=t_dt)
        
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
        logger.exception("Transit hesaplama hatası:")
        raise HTTPException(status_code=500, detail=f"Transit hesaplama hatası: {str(e)}")


@router.post("/synastry", summary="Sinastri (İlişki Uyumu) Analizi")
async def get_synastry(req: SynastryRequest, db: AsyncSession = Depends(get_db)):
    """
    İki kişinin doğum verileri üzerinden sinastri (uyum) analizi ve LLM yorumu üretir.
    """
    try:
        data_a = req.person_a_data.model_dump()
        data_b = req.person_b_data.model_dump()

        synastry_data = astro_engine.calculate_synastry(data_a, data_b)
        prompt = astro_engine.build_synastry_prompt(
            data_a,
            data_b,
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
        logger.exception("Sinastri hesaplama hatası:")
        raise HTTPException(status_code=500, detail=f"Sinastri hesaplama hatası: {str(e)}")


@router.post("/save-chart", response_model=SavedChartResponse, summary="Doğum Haritasını Kaydet")
async def save_chart(
    payload: SaveChartRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Oturum açmış kullanıcının profilinde bir doğum haritasını veritabanına saklar.
    """
    try:
        bdata = payload.birth_data
        new_chart = SavedChart(
            user_id=current_user.id,
            title=payload.title,
            year=bdata.year,
            month=bdata.month,
            day=bdata.day,
            hour=bdata.hour,
            minute=bdata.minute,
            lat=bdata.lat,
            lon=bdata.lon,
            timezone_str=bdata.timezone_str,
        )
        db.add(new_chart)
        await db.commit()
        await db.refresh(new_chart)
        return new_chart
    except Exception as e:
        logger.exception("Harita kaydetme hatası:")
        raise HTTPException(status_code=500, detail=f"Harita kaydedilemedi: {str(e)}")


@router.get("/my-charts", response_model=List[SavedChartResponse], summary="Kullanıcının Kayıtlı Haritalarını Listele")
async def get_my_charts(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Giriş yapmış kullanıcının hesabına kayıtlı tüm haritaları getirir.
    """
    result = await db.execute(select(SavedChart).where(SavedChart.user_id == current_user.id))
    charts = result.scalars().all()
    return charts


@router.delete("/charts/{chart_id}", summary="Kayıtlı Haritayı Sil")
async def delete_chart(
    chart_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Kullanıcının kaydedilmiş bir haritasını veritabanından siler.
    """
    result = await db.execute(
        select(SavedChart).where(SavedChart.id == chart_id, SavedChart.user_id == current_user.id)
    )
    chart = result.scalar_one_or_none()
    if not chart:
        raise HTTPException(status_code=404, detail="Harita bulunamadı veya silme yetkiniz yok.")

    await db.delete(chart)
    await db.commit()
    return {"status": "success", "message": "Harita başarıyla silindi."}