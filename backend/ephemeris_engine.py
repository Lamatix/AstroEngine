import swisseph as swe

ZODIAC_SIGNS = [
    "Koç", "Boğa", "İkizler", "Yengeç", 
    "Aslan", "Başak", "Terazi", "Akrep", 
    "Yay", "Oğlak", "Kova", "Balık"
]

def get_zodiac_sign(degrees: float):
    sign_index = int(degrees // 30) % 12
    sign_deg = degrees % 30
    return ZODIAC_SIGNS[sign_index], round(sign_deg, 2)

def calculate_natal_chart(year: int, month: int, day: int, hour: float, lat: float, lon: float, tz_offset: float = 3.0):
    # Yerel saati Universal Time'a (UT) çevir (Türkiye yaz saati için tz_offset = 3.0)
    ut_hour = hour - tz_offset
    
    # Julian Günü hesabı (UT bazlı)
    jd = swe.julday(year, month, day, ut_hour)
    
    # Gezegen pozisyonları
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
    
    # Evler ve Yükselen (Ascendant / MC) Hesabı ('P' = Placidus ev sistemi)
    houses, ascmc = swe.houses(jd, lat, lon, b'P')
    asc_longitude = ascmc[0] # Yükselen Derecesi
    asc_sign, asc_deg = get_zodiac_sign(asc_longitude)
    
    mc_longitude = ascmc[1] # Tepe Noktası (Midheaven)
    mc_sign, mc_deg = get_zodiac_sign(mc_longitude)

    return {
        "julian_day": jd,
        "ut_hour_used": ut_hour,
        "angles": {
            "Yükselen (Ascendant)": {"longitude": round(asc_longitude, 2), "sign": asc_sign, "degree_in_sign": asc_deg},
            "Tepe Noktası (MC)": {"longitude": round(mc_longitude, 2), "sign": mc_sign, "degree_in_sign": mc_deg}
        },
        "planets": results
    }