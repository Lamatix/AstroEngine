from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from app.services.astro_engine import astro_engine  # AstroEngine servisinin doğru yoldan import edildiğinden emin ol

router = APIRouter(prefix="/api/v1", tags=["Transit Analizi"])

class BirthDataModel(BaseModel):
    year: int = Field(..., example=1987)
    month: int = Field(..., example=7)
    day: int = Field(..., example=14)
    hour: int = Field(..., example=18)
    minute: int = Field(..., example=30)
    lat: float = Field(..., example=41.0082)
    lon: float = Field(..., example=28.9784)
    tz_offset: float = Field(None, example=3.0)
    timezone: str = Field("Europe/Istanbul", example="Europe/Istanbul")
    house_system: str = Field("P", example="P")

class TransitRequestModel(BaseModel):
    birth_data: BirthDataModel
    transit_date: str = Field(None, description="Format: YYYY-MM-DD HH:MM (Boş bırakılırsa şuanın tarihi alınır)", example="2026-09-24 12:00")

@router.post("/transit")
def calculate_transit_endpoint(payload: TransitRequestModel):
    try:
        # Pydantic modelini dict'e çevir
        birth_dict = payload.birth_data.dict()
        
        # Transit tarihini ayarla
        t_dt = None
        if payload.transit_date:
            t_dt = datetime.strptime(payload.transit_date, "%Y-%m-%d %H:%M")
            
        # AstroEngine ile transit hesaplamasını yap
        transit_result = astro_engine.calculate_transits(birth_dict, t_dt)
        
        # Yapay zeka promptunu da opsiyonel olarak çıktıya ekleyebiliriz (isteğe bağlı)
        ai_prompt = astro_engine.build_transit_prompt(birth_dict, t_dt)

        return {
            "success": True,
            "data": transit_result,
            "ai_prompt": ai_prompt
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))