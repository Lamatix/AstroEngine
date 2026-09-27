import os
import swisseph as swe
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

class AstroEngine:
    ASPECTS = {
        "Kavuşum (0°)": {"angle": 0, "orb": 8},
        "Sekstil (60°)": {"angle": 60, "orb": 6},
        "Kare (90°)": {"angle": 90, "orb": 8},
        "Üçgen (120°)": {"angle": 120, "orb": 8},
        "Karşıt (180°)": {"angle": 180, "orb": 8}
    }

    def __init__(self, ephe_path: str = None):
        if ephe_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))  # app/services
            app_dir = os.path.dirname(current_dir)                    # app
            ephe_dir = os.path.join(app_dir, "ephe")                  # app/ephe
        else:
            ephe_dir = os.path.abspath(ephe_path)

        swe.set_ephe_path(ephe_dir)

        chiron_file = os.path.join(ephe_dir, "seas_18.se1")
        print(f"[AstroEngine] Ephemeris Dizin Yolu: {ephe_dir}")
        print(f"[AstroEngine] Chiron Dosyası Var mı?: {os.path.exists(chiron_file)}")

    def degree_to_zodiac(self, degree: float) -> str:
        """Dereceyi burç ve derece formatına dönüştürür."""
        if degree is None:
            return "Hesaplanamadı (Ephemeris Dosyası Eksik)"
            
        signs = [
            "Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak", 
            "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"
        ]
        index = int(degree // 30) % 12
        deg_in_sign = degree % 30
        return f"{signs[index]} ({int(deg_in_sign)}°)"

    def get_planet_house(self, planet_deg: float, cusps: list) -> int:
        """Gezegenin derecesine ve ev çizgilerine (cusps) göre hangi evde olduğunu bulur (1-12)."""
        if planet_deg is None or not cusps or len(cusps) < 12:
            return None
            
        for i in range(12):
            c1 = cusps[i]
            c2 = cusps[(i + 1) % 12]
            if c1 < c2:
                if c1 <= planet_deg < c2:
                    return i + 1
            else:  # Zodyak 0° (Koç) noktasını kapsayan geçiş evi
                if planet_deg >= c1 or planet_deg < c2:
                    return i + 1
        return 1

    def _calc_body(self, julian_day: float, body_code: int) -> dict:
        """Gezegen, asteroit veya hassas noktaların konumunu ve retro durumunu hesaplar."""
        try:
            pos, _ = swe.calc_ut(julian_day, body_code, swe.FLG_SWIEPH | swe.FLG_SPEED)
            return {
                "degree": pos[0],
                "is_retro": pos[3] < 0
            }
        except Exception:
            if body_code == swe.CHIRON:
                try:
                    chiron_id = swe.AST_OFFSET + 2060
                    pos, _ = swe.calc_ut(julian_day, chiron_id, swe.FLG_SWIEPH | swe.FLG_SPEED)
                    return {
                        "degree": pos[0],
                        "is_retro": pos[3] < 0
                    }
                except Exception:
                    pass

            # Lilith (Mean Apogee - Swiss Ephemeris sabiti 12) için güvenli fallback
            if body_code == 12:
                try:
                    pos, _ = swe.calc_ut(julian_day, 12, swe.FLG_SWIEPH | swe.FLG_SPEED)
                    return {
                        "degree": pos[0],
                        "is_retro": pos[3] < 0
                    }
                except Exception:
                    pass

            try:
                pos, _ = swe.calc_ut(julian_day, body_code, swe.FLG_MOSEPH | swe.FLG_SPEED)
                return {
                    "degree": pos[0],
                    "is_retro": pos[3] < 0
                }
            except Exception:
                return {"degree": None, "is_retro": False}

    def calculate_aspects(self, planets_data: dict) -> list:
        """Gezegen dereceleri arasındaki majör açıları ve orbları hesaplar."""
        aspects_found = []
        valid_planets = {k: v["degree"] for k, v in planets_data.items() if v.get("degree") is not None}
        planet_names = list(valid_planets.keys())

        for i in range(len(planet_names)):
            for j in range(i + 1, len(planet_names)):
                p1_name = planet_names[i]
                p2_name = planet_names[j]

                deg1 = valid_planets[p1_name]
                deg2 = valid_planets[p2_name]

                diff = abs(deg1 - deg2)
                if diff > 180:
                    diff = 360 - diff

                for asp_name, asp_info in self.ASPECTS.items():
                    target_angle = asp_info["angle"]
                    max_orb = asp_info["orb"]

                    orb = abs(diff - target_angle)
                    if orb <= max_orb:
                        aspects_found.append({
                            "p1": p1_name,
                            "p2": p2_name,
                            "aspect": asp_name,
                            "orb": round(orb, 2),
                            "exact_angle": round(diff, 2)
                        })

        return aspects_found

    def calculate_natal_chart(
        self, 
        year: int, 
        month: int, 
        day: int, 
        hour: int, 
        minute: int, 
        lat: float, 
        lon: float,
        tz_offset: float = None,
        timezone_str: str = "Europe/Istanbul",
        house_system: str = "P"
    ) -> dict:
        local_dt = datetime(year, month, day, hour, minute)

        if tz_offset is None:
            tz_aware = local_dt.replace(tzinfo=ZoneInfo(timezone_str))
            tz_offset = tz_aware.utcoffset().total_seconds() / 3600.0

        utc_dt = local_dt - timedelta(hours=tz_offset)

        utc_decimal_hour = utc_dt.hour + (utc_dt.minute / 60.0) + (utc_dt.second / 3600.0)
        julian_day = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_decimal_hour)

        bodies = {
            "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
            "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
            "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE,
            "Pluto": swe.PLUTO, "North_Node": swe.TRUE_NODE, "Chiron": swe.CHIRON,
            "Lilith": 12, "Ceres": swe.CERES, "Pallas": swe.PALLAS,
            "Juno": swe.JUNO, "Vesta": swe.VESTA
        }

        planets = {}
        for name, code in bodies.items():
            planets[name] = self._calc_body(julian_day, code)

        if planets["North_Node"]["degree"] is not None:
            planets["South_Node"] = {
                "degree": (planets["North_Node"]["degree"] + 180.0) % 360.0,
                "is_retro": planets["North_Node"]["is_retro"]
            }
        else:
            planets["South_Node"] = {"degree": None, "is_retro": False}

        h_sys = house_system.encode('utf-8')
        cusps, ascmc = swe.houses(julian_day, lat, lon, h_sys)
        cusps_list = list(cusps)

        for name in planets:
            deg = planets[name]["degree"]
            planets[name]["house"] = self.get_planet_house(deg, cusps_list)

        aspects = self.calculate_aspects(planets)

        return {
            "julian_day": julian_day,
            "ascendant": ascmc[0],
            "mc": ascmc[1],
            "cusps": cusps_list,
            "planets": planets,
            "aspects": aspects,
            "location": {"lat": lat, "lon": lon, "tz_offset": tz_offset, "timezone": timezone_str}
        }

    def calculate_transits(self, birth_data: dict, transit_dt: datetime = None) -> dict:
        """Belirli bir tarihteki transit gezegenlerin doğum haritası üzerindeki etkilerini hesaplar."""
        if transit_dt is None:
            transit_dt = datetime.now()

        natal_chart = self.calculate_natal_chart(**birth_data)

        transit_jd = swe.julday(
            transit_dt.year, transit_dt.month, transit_dt.day,
            transit_dt.hour + (transit_dt.minute / 60.0) + (transit_dt.second / 3600.0)
        )

        bodies = {
            "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
            "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
            "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE,
            "Pluto": swe.PLUTO, "Chiron": swe.CHIRON, "North_Node": swe.TRUE_NODE
        }

        transit_planets = {}
        for name, code in bodies.items():
            t_data = self._calc_body(transit_jd, code)
            t_data["natal_house"] = self.get_planet_house(t_data["degree"], natal_chart["cusps"])
            transit_planets[name] = t_data

        transit_aspects = []
        for t_name, t_info in transit_planets.items():
            t_deg = t_info["degree"]
            if t_deg is None:
                continue

            for n_name, n_info in natal_chart["planets"].items():
                n_deg = n_info["degree"]
                if n_deg is None:
                    continue

                diff = abs(t_deg - n_deg)
                if diff > 180:
                    diff = 360 - diff

                for asp_name, asp_info in self.ASPECTS.items():
                    target_angle = asp_info["angle"]
                    max_orb = asp_info["orb"]

                    orb = abs(diff - target_angle)
                    if orb <= max_orb:
                        transit_aspects.append({
                            "transit_planet": t_name,
                            "natal_planet": n_name,
                            "aspect": asp_name,
                            "orb": round(orb, 2),
                            "transit_house": t_info["natal_house"]
                        })

        return {
            "natal_chart": natal_chart,
            "transit_date": transit_dt.strftime("%Y-%m-%d %H:%M"),
            "transit_planets": transit_planets,
            "transit_aspects": transit_aspects
        }

    def calculate_synastry(self, person_a_data: dict, person_b_data: dict) -> dict:
        """İki kişinin doğum haritalarını karşılaştırarak Sinastri açılarını ve ev düşüşlerini hesaplar."""
        chart_a = self.calculate_natal_chart(**person_a_data)
        chart_b = self.calculate_natal_chart(**person_b_data)

        synastry_aspects = []
        planets_a = chart_a["planets"]
        planets_b = chart_b["planets"]

        for name_a, info_a in planets_a.items():
            deg_a = info_a.get("degree")
            if deg_a is None:
                continue

            for name_b, info_b in planets_b.items():
                deg_b = info_b.get("degree")
                if deg_b is None:
                    continue

                diff = abs(deg_a - deg_b)
                if diff > 180:
                    diff = 360 - diff

                for asp_name, asp_info in self.ASPECTS.items():
                    target_angle = asp_info["angle"]
                    max_orb = asp_info["orb"]

                    orb = abs(diff - target_angle)
                    if orb <= max_orb:
                        synastry_aspects.append({
                            "planet_a": name_a,
                            "planet_b": name_b,
                            "aspect": asp_name,
                            "orb": round(orb, 2)
                        })

        a_in_b_houses = {}
        for name_a, info_a in planets_a.items():
            if info_a.get("degree") is not None:
                a_in_b_houses[name_a] = self.get_planet_house(info_a["degree"], chart_b["cusps"])

        b_in_a_houses = {}
        for name_b, info_b in planets_b.items():
            if info_b.get("degree") is not None:
                b_in_a_houses[name_b] = self.get_planet_house(info_b["degree"], chart_a["cusps"])

        return {
            "chart_a": chart_a,
            "chart_b": chart_b,
            "synastry_aspects": synastry_aspects,
            "a_in_b_houses": a_in_b_houses,
            "b_in_a_houses": b_in_a_houses
        }

    def build_astrology_prompt(self, birth_data: dict) -> str:
        tz_offset = birth_data.get("tz_offset", None)
        timezone_str = birth_data.get("timezone", "Europe/Istanbul")
        house_system = birth_data.get("house_system", "P")

        chart = self.calculate_natal_chart(
            year=birth_data["year"],
            month=birth_data["month"],
            day=birth_data["day"],
            hour=birth_data["hour"],
            minute=birth_data["minute"],
            lat=birth_data["lat"],
            lon=birth_data["lon"],
            tz_offset=tz_offset,
            timezone_str=timezone_str,
            house_system=house_system
        )

        p = chart["planets"]
        aspects = chart["aspects"]

        def format_body(name: str) -> str:
            info = p.get(name, {})
            deg = info.get("degree")
            retro_str = " [Rx]" if info.get("is_retro") else ""
            house = f" | {info.get('house')}. Ev" if info.get('house') else ""
            return f"{self.degree_to_zodiac(deg)}{retro_str}{house}"

        aspects_text = ""
        if aspects:
            for asp in aspects:
                aspects_text += f"- {asp['p1']} ve {asp['p2']}: {asp['aspect']} (Orb: {asp['orb']}°)\n"
        else:
            aspects_text = "- Belirgin bir majör açı bulunamadı.\n"

        return f"""
Aşağıdaki KESİN astronomik doğum haritası verilerini kullanarak derinlemesine ve kapsamlı bir astroloji analizi yap:

--- ANA HARİTA NOKTALARI ---
- Yükselen Burç (ASC): {self.degree_to_zodiac(chart['ascendant'])}
- Tepe Noktası (MC): {self.degree_to_zodiac(chart['mc'])}
- Zaman Dilimi (Offset): UTC+{chart['location']['tz_offset']} ({chart['location']['timezone']})

--- GEZEGEN KONUMLARI VE EVLER ---
- Güneş: {format_body('Sun')}
- Ay: {format_body('Moon')}
- Merkür: {format_body('Mercury')}
- Venüs: {format_body('Venus')}
- Mars: {format_body('Mars')}
- Jüpiter: {format_body('Jupiter')}
- Satürn: {format_body('Saturn')}
- Uranüs: {format_body('Uranus')}
- Neptün: {format_body('Neptune')}
- Plüton: {format_body('Pluto')}

--- KADERSEL NOKTALAR VE ASTEROİTLER ---
- Kuzey Ay Düğümü (KAD): {format_body('North_Node')}
- Güney Ay Düğümü (GAD): {format_body('South_Node')}
- Chiron (Kiron): {format_body('Chiron')}
- Lilith (Kara Ay): {format_body('Lilith')}
- Ceres: {format_body('Ceres')}
- Pallas: {format_body('Pallas')}
- Juno: {format_body('Juno')}
- Vesta: {format_body('Vesta')}

--- MAJÖR AÇILAR (ASPECTS) ---
{aspects_text.strip()}

Lütfen hesaplamaları sorgulamadan, doğrudan sana verilen bu kesin gezegen, ev, retro durumlarına, asteroit konumlarına ve açılara sadık kalarak karakter, potansiyel ve karmik analiz yap.
""".strip()

    def build_transit_prompt(self, birth_data: dict, transit_dt: datetime = None) -> str:
        transit_data = self.calculate_transits(birth_data, transit_dt)
        t_planets = transit_data["transit_planets"]
        t_aspects = transit_data["transit_aspects"]

        t_positions_text = ""
        for name, info in t_planets.items():
            retro_str = " [Rx]" if info["is_retro"] else ""
            t_positions_text += f"- Transit {name}: {self.degree_to_zodiac(info['degree'])}{retro_str} -> Natal {info['natal_house']}. Evde\n"

        t_aspects_text = ""
        if t_aspects:
            for asp in t_aspects:
                t_aspects_text += f"- Transit {asp['transit_planet']} ({asp['transit_house']}. Ev) -> Natal {asp['natal_planet']}: {asp['aspect']} (Orb: {asp['orb']}°)\n"
        else:
            t_aspects_text = "- Belirgin bir transit açısı bulunamadı.\n"

        return f"""
Aşağıdaki KESİN transit verilerini ve doğum haritası etkileşimlerini kullanarak günlük/dönemsel öngörü analizi yap:

--- TRANSİT TARİHİ ---
{transit_data['transit_date']}

--- TRANSİT GEZEGENLERİN DURUMU VE NATAL EV GEÇİŞLERİ ---
{t_positions_text.strip()}

--- TRANSİT GEZEGENLERİN NATAL GEZEGENLERLE YAPTIĞI AÇILAR ---
{t_aspects_text.strip()}

Bu verilere dayanarak kişinin mevcut dönemdeki ruh halini, kariyer, ilişki ve fırsat/fırtına alanlarını detaylıca yorumla.
""".strip()

    def build_synastry_prompt(self, person_a_data: dict, person_b_data: dict, name_a: str = "Kişi A", name_b: str = "Kişi B") -> str:
        syn_data = self.calculate_synastry(person_a_data, person_b_data)
        aspects = syn_data["synastry_aspects"]
        a_in_b = syn_data["a_in_b_houses"]
        b_in_a = syn_data["b_in_a_houses"]

        aspects_text = ""
        if aspects:
            for asp in aspects:
                aspects_text += f"- {name_a} {asp['planet_a']} <--> {name_b} {asp['planet_b']}: {asp['aspect']} (Orb: {asp['orb']}°)\n"
        else:
            aspects_text = "- Belirgin bir sinastri açısı bulunamadı.\n"

        overlays_text = f"--- {name_a}'nın Gezegenlerinin {name_b}'nin Evlerindeki Konumu ---\n"
        for p_name, house_num in a_in_b.items():
            overlays_text += f"- {name_a} {p_name} -> {name_b}'nin {house_num}. Evinde\n"

        overlays_text += f"\n--- {name_b}'nin Gezegenlerinin {name_a}'nın Evlerindeki Konumu ---\n"
        for p_name, house_num in b_in_a.items():
            overlays_text += f"- {name_b} {p_name} -> {name_a}'nın {house_num}. Evinde\n"

        return f"""
Aşağıdaki KESİN Sinastri (İlişki Uyumu) verilerini kullanarak iki kişi arasındaki ilişki dinamiğini detaylıca yorumla:

--- SİNASTRİ AÇILARI ({name_a} & {name_b}) ---
{aspects_text.strip()}

--- EV DÜŞÜŞLERİ (HOUSE OVERLAYS) ---
{overlays_text.strip()}

Lütfen bu verilere sadık kalarak ikilinin:
1. Duygusal ve Zihinsel Uyumunu (Ay, Merkür, Venüs temasları)
2. Çekim ve Tutku Dinamiğini (Mars, Venüs, Plüton temasları)
3. Uzun Vadeli Bağ ve Karmik Bağlarını (Satürn, Ay Düğümleri, Kiron temasları)
4. Potansiyel Çalışma veya Kriz Alanlarını detaylıca analiz et.
""".strip()

astro_engine = AstroEngine()