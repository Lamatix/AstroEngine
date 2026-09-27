from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ephemeris_engine import calculate_natal_chart

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

@app.get("/health")
def health_check():
    return {"status": "healthy", "engine": "Swiss Ephemeris & SaaS Core Active"}