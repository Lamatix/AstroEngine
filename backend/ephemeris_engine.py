import swisseph as swe
from datetime import datetime

ZODIAC_SIGNS = [
    "Koç", "Boğa", "İkizler", "Yengeç", 
    "Aslan", "Başak", "Terazi", "Akrep", 
    "Yay", "Oğlak", "Kova", "Balık"
]

def get_zodiac_sign(degrees: float):
    sign_index = int(degrees // 30)
    sign_deg = degrees % 30
    return ZODIAC_SIGNS[sign_index], round(sign_deg, 2)

def calculate_natal_chart(year: int, month: int, day: int, hour: float, lat: float, lon: float):
    # Julian Günü hesabı (UT bazlı)
    jd = swe.julday(year, month, day, hour)
    
    planets = {
        "Güneş": swe.SUN,
        "Ay": swe.MOON,
        "Merkür": swe.MERCURY,
        "Venüs": swe.VENUS,
        "Mars": swe.MARS,
        "Jüpiter": swe.JUPITER,
        "Satürn": swe.SATURN,
        "Uranüs": swe.URANUS,
        "Neptün": swe.NEPTUNE,
        "Plüton": swe.PLUTO
    }
    
    results = {}
    for name, p_id in planets.items():
        pos, ret = swe.calc_ut(jd, p_id)
        longitude = pos[0]
        sign, deg = get_zodiac_sign(longitude)
        
        results[name] = {
            "longitude": round(longitude, 2),
            "sign": sign,
            "degree_in_sign": deg,
            "is_retrograde": pos[3] < 0
        }
        
    return {
        "julian_day": jd,
        "planets": results
    }