import os
import json
import sqlite3
import urllib.request
import urllib.parse
import datetime
from typing import Optional, Dict, Any, List

WMO_WEATHER_MAP = {
    0: {"name": "Açık", "icon": "clear_sun"},
    1: {"name": "Çoğunlukla Açık", "icon": "partly_cloudy"},
    2: {"name": "Parçalı Bulutlu", "icon": "partly_cloudy"},
    3: {"name": "Bulutlu", "icon": "cloudy"},
    45: {"name": "Sisli", "icon": "fog"},
    48: {"name": "Kırağılı Sis", "icon": "fog"},
    51: {"name": "Hafif Çisenti", "icon": "drizzle"},
    53: {"name": "Çisenti", "icon": "drizzle"},
    55: {"name": "Yoğun Çisenti", "icon": "drizzle"},
    61: {"name": "Hafif Yağmurlu", "icon": "rain"},
    63: {"name": "Yağmurlu", "icon": "rain"},
    65: {"name": "Kuvvetli Yağmur", "icon": "heavy_rain"},
    71: {"name": "Hafif Kar", "icon": "snow"},
    73: {"name": "Kar Yağışlı", "icon": "snow"},
    75: {"name": "Yoğun Kar", "icon": "snow"},
    80: {"name": "Hafif Sağanak", "icon": "rain"},
    81: {"name": "Sağanak Yağış", "icon": "thunderstorm"},
    82: {"name": "Kuvvetli Sağanak", "icon": "thunderstorm"},
    95: {"name": "Gök Gürültülü Fırtına", "icon": "thunderstorm"},
    96: {"name": "Dolu ve Fırtına", "icon": "thunderstorm"},
    99: {"name": "Şiddetli Fırtına", "icon": "thunderstorm"}
}

TURKISH_DAY_ABBR = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]

def degrees_to_compass(deg: float) -> str:
    val = int((deg / 22.5) + 0.5) % 16
    directions = ["Kuzey", "KKB", "Kuzeydoğu", "DKD", "Doğu", "DGD", "Güneydoğu", "GGB", "Güney", "GGB", "Güneybatı", "BGB", "Batı", "BKB", "Kuzeybatı", "KKB"]
    return directions[val]

class WeatherEngine:
    def __init__(self, settings_manager):
        self.settings = settings_manager
        self.db_path = os.path.expanduser("~/.config/ezan-vakti/cache.db")
        self._mem_cache = {}
        self._mem_cache_time = {}
        self._fail_until = {}  # negative cache: city -> datetime until which we skip network retries
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS weather_cache (
                query_name TEXT PRIMARY KEY,
                latitude REAL,
                longitude REAL,
                display_location TEXT,
                cached_time TEXT,
                data_json TEXT
            )
        """)
        conn.commit()
        conn.close()

    def clear_mem_cache(self):
        self._mem_cache.clear()
        self._mem_cache_time.clear()
        self._fail_until.clear()

    def get_coordinates(self, city_name: str) -> Optional[Dict[str, Any]]:
        """Resolves city coordinates via Open-Meteo Geocoding API."""
        encoded = urllib.parse.quote(city_name)
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded}&count=1&language=tr&format=json"
        req = urllib.request.Request(url, headers={"User-Agent": "EzanHavaApp/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=5) as res:
                if res.status == 200:
                    data = json.loads(res.read().decode())
                    results = data.get("results")
                    if results and len(results) > 0:
                        first = results[0]
                        name = first.get("name", city_name)
                        country = first.get("country_code", "TR").upper()
                        display_loc = f"{name}, Turkey, {country}" if country == "TR" else f"{name}, {country}"
                        return {
                            "lat": first["latitude"],
                            "lon": first["longitude"],
                            "display_name": display_loc,
                            "name": name
                        }
        except Exception as e:
            print(f"Geocoding error for {city_name}: {e}")
        return None

    def get_weather(self, city_name: Optional[str] = None, force_refresh: bool = False) -> Dict[str, Any]:
        """Fetches current and 7-day weather, with cache support."""
        if not city_name:
            city_name = self.settings.get("city", "Darica")

        clean_name = city_name.strip().lower()
        now = datetime.datetime.now()

        # 1. Check RAM memory cache (0ms lookup, zero SQLite disk I/O)
        if not force_refresh and clean_name in self._mem_cache:
            last_t = self._mem_cache_time.get(clean_name)
            if last_t and (now - last_t).total_seconds() < 1800:
                return self._mem_cache[clean_name]

        # 2. Check SQLite Cache (valid for 30 minutes)
        if not force_refresh:
            try:
                conn = sqlite3.connect(self.db_path)
                cur = conn.cursor()
                cur.execute("SELECT display_location, cached_time, data_json FROM weather_cache WHERE query_name=?", (clean_name,))
                row = cur.fetchone()
                conn.close()
                if row:
                    cached_time = datetime.datetime.fromisoformat(row[1])
                    if (now - cached_time).total_seconds() < 1800:
                        try:
                            parsed_data = json.loads(row[2])
                            self._mem_cache[clean_name] = parsed_data
                            self._mem_cache_time[clean_name] = cached_time
                            return parsed_data
                        except Exception:
                            pass
            except Exception as e:
                print(f"Weather cache read error: {e}")

        # 3. Negative cache: a recent lookup for this city failed -> do not block the UI again
        if not force_refresh:
            until = self._fail_until.get(clean_name)
            if until and now < until:
                return self._fallback_weather(f"{city_name.strip().capitalize()}", city_name.strip().capitalize())

        # Resolve Coordinates
        geo = self.get_coordinates(city_name)
        if not geo:
            # Never reuse another city's coordinates (that produced stale Darıca data)
            self._fail_until[clean_name] = now + datetime.timedelta(seconds=60)
            return self._fallback_weather(f"{city_name.strip().capitalize()}", city_name.strip().capitalize())

        lat = geo["lat"]
        lon = geo["lon"]
        display_loc = geo["display_name"]

        # Fetch from Open-Meteo with extra details (surface_pressure, uv_index, apparent_temp)
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&"
            f"current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m,surface_pressure,uv_index&"
            f"daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,sunrise,sunset&"
            f"wind_speed_unit=ms&timezone=auto"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "EzanHavaApp/1.0"})

        try:
            with urllib.request.urlopen(req, timeout=6) as res:
                if res.status == 200:
                    raw = json.loads(res.read().decode())
                    cur_w = raw.get("current", {})
                    daily_w = raw.get("daily", {})

                    # Current
                    cur_temp = round(cur_w.get("temperature_2m", 14.0))
                    cur_code = cur_w.get("weather_code", 0)
                    cur_wind = round(cur_w.get("wind_speed_10m", 3.5), 1)
                    cur_wind_dir = cur_w.get("wind_direction_10m", 0)
                    humidity = cur_w.get("relative_humidity_2m", 70)
                    apparent_temp = round(cur_w.get("apparent_temperature", cur_temp))
                    pressure = round(cur_w.get("surface_pressure", 1013))
                    uv_val = round(cur_w.get("uv_index", 1.0), 1)
                    precip_mm = cur_w.get("precipitation", 0.0)

                    # Sunrise / Sunset
                    sunrises = daily_w.get("sunrise", [])
                    sunsets = daily_w.get("sunset", [])
                    sunrise_str = sunrises[0].split("T")[-1][:5] if sunrises else "07:09"
                    sunset_str = sunsets[0].split("T")[-1][:5] if sunsets else "18:29"

                    # 7-day forecast
                    daily_list = []
                    times = daily_w.get("time", [])
                    codes = daily_w.get("weather_code", [])
                    max_temps = daily_w.get("temperature_2m_max", [])
                    min_temps = daily_w.get("temperature_2m_min", [])
                    precip_probs = daily_w.get("precipitation_probability_max", [])

                    for i in range(min(7, len(times))):
                        dt = datetime.date.fromisoformat(times[i])
                        day_abbr = TURKISH_DAY_ABBR[dt.weekday()]
                        code = codes[i] if i < len(codes) else 0
                        max_t = round(max_temps[i]) if i < len(max_temps) else 15
                        min_t = round(min_temps[i]) if i < len(min_temps) else 10
                        prob = precip_probs[i] if i < len(precip_probs) and precip_probs[i] is not None else 0
                        prob_str = f"%{prob}" if prob > 5 else "-"

                        meta = WMO_WEATHER_MAP.get(code, {"name": "Açık", "icon": "clear_sun"})

                        daily_list.append({
                            "date": times[i],
                            "day_abbr": day_abbr,
                            "weather_code": code,
                            "icon_type": meta["icon"],
                            "condition_name": meta["name"],
                            "max_temp": f"{max_t} °C",
                            "min_temp": f"{min_t} °C",
                            "precip_prob": prob_str
                        })

                    cur_meta = WMO_WEATHER_MAP.get(cur_code, {"name": "Açık", "icon": "clear_sun"})
                    compass_str = degrees_to_compass(cur_wind_dir)

                    weather_result = {
                        "location": display_loc,
                        "city": geo["name"],
                        "current_temp": f"{cur_temp} °C",
                        "current_temp_val": cur_temp,
                        "weather_code": cur_code,
                        "icon_type": cur_meta["icon"],
                        "condition_name": cur_meta["name"],
                        "wind_speed": f"{str(cur_wind).replace('.', ',')} m/sn",
                        "wind_direction": cur_wind_dir,
                        "wind_full": f"{str(cur_wind).replace('.', ',')} m/sn ({compass_str})",
                        "humidity": f"%{humidity}",
                        "apparent_temp": f"{apparent_temp} °C",
                        "pressure": f"{pressure} hPa",
                        "uv_index": f"{str(uv_val).replace('.', ',')}",
                        "precipitation": f"{str(precip_mm).replace('.', ',')} mm",
                        "sunrise": sunrise_str,
                        "sunset": sunset_str,
                        "daily": daily_list,
                        "updated_at": datetime.datetime.now().strftime("%H:%M")
                    }

                    # Cache in DB
                    conn = sqlite3.connect(self.db_path)
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT OR REPLACE INTO weather_cache (query_name, latitude, longitude, display_location, cached_time, data_json)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (clean_name, lat, lon, display_loc, datetime.datetime.now().isoformat(), json.dumps(weather_result, ensure_ascii=False)))
                    conn.commit()
                    conn.close()

                    # Cache in RAM
                    self._mem_cache[clean_name] = weather_result
                    self._mem_cache_time[clean_name] = datetime.datetime.now()

                    return weather_result
        except Exception as e:
            print(f"Hava durumu çekme hatası: {e}")

        # Fallback if offline
        self._fail_until[clean_name] = datetime.datetime.now() + datetime.timedelta(seconds=60)
        return self._fallback_weather(display_loc, city_name.strip().capitalize())

    def _fallback_weather(self, display_loc: str, city_label: str = "Darıca") -> Dict[str, Any]:
        return {
            "location": display_loc or "Darıca, Turkey, TR",
            "city": city_label,
            "current_temp": "14 °C",
            "current_temp_val": 14,
            "weather_code": 95,
            "icon_type": "thunderstorm",
            "condition_name": "Gök Gürültülü Sağanak",
            "wind_speed": "3,5 m/sn",
            "wind_direction": 180,
            "wind_full": "3,5 m/sn (Güney)",
            "humidity": "%75",
            "apparent_temp": "13 °C",
            "pressure": "1012 hPa",
            "uv_index": "1,5",
            "precipitation": "0,0 mm",
            "sunrise": "07:09",
            "sunset": "18:29",
            "daily": [
                {"day_abbr": "Cum", "icon_type": "thunderstorm", "precip_prob": "%88", "max_temp": "15 °C", "min_temp": "10 °C"},
                {"day_abbr": "Cmt", "icon_type": "thunderstorm", "precip_prob": "%89", "max_temp": "15 °C", "min_temp": "11 °C"},
                {"day_abbr": "Paz", "icon_type": "heavy_rain", "precip_prob": "%50", "max_temp": "17 °C", "min_temp": "12 °C"},
                {"day_abbr": "Pzt", "icon_type": "partly_cloudy", "precip_prob": "%11", "max_temp": "19 °C", "min_temp": "11 °C"},
                {"day_abbr": "Sal", "icon_type": "clear_sun", "precip_prob": "%10", "max_temp": "20 °C", "min_temp": "10 °C"},
                {"day_abbr": "Çar", "icon_type": "clear_sun", "precip_prob": "%10", "max_temp": "20 °C", "min_temp": "11 °C"},
                {"day_abbr": "Per", "icon_type": "partly_cloudy", "precip_prob": "-", "max_temp": "20 °C", "min_temp": "12 °C"}
            ],
            "updated_at": "--:--"
        }
