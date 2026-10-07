from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Any
from ephemeris_engine import calculate_natal_chart
from llm_service import llm_service

app = FastAPI(title="AstroEngine Production API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Üretimde Vercel domain adresimizle sınırlandırılacak
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BirthData(BaseModel):
    year: int
    month: int
    day: int
    hour: float
    latitude: float
    longitude: float
    timezone: Optional[float] = 3.0  # Varsayılan Türkiye GMT+3

class AstrologyInterpretationRequest(BaseModel):
    birth_data: BirthData
    client_name: Optional[str] = "Danışan"

class AutomationTask(BaseModel):
    task_type: Optional[str] = None
    store_id: Optional[str] = None
    row_number: Optional[Any] = None
    # n8n'den gelebilecek esnek ek alanlar için
    extra_data: Optional[dict] = None

@app.post("/api/calculate-radix")
def api_calculate_radix(data: BirthData):
    try:
        chart = calculate_natal_chart(
            data.year, data.month, data.day, 
            data.hour, data.latitude, data.longitude
        )
        return {"status": "success", "data": chart}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/astrology/interpret")
def api_interpret_astrology(payload: AstrologyInterpretationRequest):
    """
    1. Adım: Swiss Ephemeris ile radiks (doğum haritası) hesaplar.
    2. Adım: Elde edilen matematiksel veriyi LLM Servisi (OpenAI ajanına) göndererek derin yorum üretir.
    """
    try:
        # 1. Ephemeris hesaplaması
        chart = calculate_natal_chart(
            payload.birth_data.year,
            payload.birth_data.month,
            payload.birth_data.day,
            payload.birth_data.hour,
            payload.birth_data.latitude,
            payload.birth_data.longitude
        )

        # 2. Yapay zeka ajanını çağırarak yorumlatma
        interpretation = llm_service.generate_astrology_interpretation(
            radix_data=chart,
            client_name=payload.client_name
        )

        return {
            "status": "success",
            "client_name": payload.client_name,
            "radix_data": chart,
            "interpretation": interpretation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/automation/execute-task")
def execute_automation_task(task: AutomationTask):
    try:
        # n8n'den gelen otomasyon görevlerini burada işleyebiliriz
        print(f"Gelen Görev: {task.task_type} | Mağaza: {task.store_id} | Satır: {task.row_number}")
        
        # Şimdilik başarılı bir yanıt dönelim
        return {
            "status": "success",
            "message": f"Task '{task.task_type}' executed successfully for store '{task.store_id}'.",
            "received_data": task.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy", "engine": "Swiss Ephemeris & AI Multi-Agent Core Active"}