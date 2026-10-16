import os
import json
import sqlite3
import urllib.request
import urllib.parse
import datetime
from typing import Optional, Dict, Any, Tuple

HIJRI_MONTHS_TR = {
    1: "Muharrem",
    2: "Sefer",
    3: "Rebiülevvel",
    4: "Rebiülahir",
    5: "Cemaziyelevvel",
    6: "Cemaziyelahir",
    7: "Recep",
    8: "Şaban",
    9: "Ramazan",
    10: "Şevval",
    11: "Zilkade",
    12: "Zilhicce"
}

PRAYER_NAMES_TR = {
    "Fajr": "İmsak",
    "Sunrise": "Güneş",
    "Dhuhr": "Öğle",
    "Asr": "İkindi",
    "Maghrib": "Akşam",
    "Isha": "Yatsı"
}

PRAYER_ORDER = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]

class PrayerEngine:
    def __init__(self, settings_manager):
        self.settings = settings_manager
        self.db_path = os.path.expanduser("~/.config/ezan-vakti/cache.db")
        self._mem_cache = {}  # Ultra-fast in-memory cache to eliminate disk I/O
        self._failed_months = {}  # (city, country, year, month) -> retry-after datetime
        self._fallback_until = {}  # (city, country) -> datetime until which fallback is served without retry
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS prayer_cache (
                city TEXT,
                country TEXT,
                date_str TEXT,
                fajr TEXT,
                sunrise TEXT,
                dhuhr TEXT,
                asr TEXT,
                maghrib TEXT,
                isha TEXT,
                hijri_day TEXT,
                hijri_month INTEGER,
                hijri_year TEXT,
                PRIMARY KEY (city, country, date_str)
            )
        """)
        conn.commit()
        conn.close()

    def clear_mem_cache(self):
        self._mem_cache.clear()
        self._failed_months.clear()
        self._fallback_until.clear()

    def _fetch_calendar_payload(self, city: str, country: str, year: int, month: int) -> Optional[list]:
        method = self.settings.get("method", 13)
        encoded_city = urllib.parse.quote(city)
        encoded_country = urllib.parse.quote(country)
        
        # 1. Try standard calendarByCity
        url_city = f"https://api.aladhan.com/v1/calendarByCity?city={encoded_city}&country={encoded_country}&method={method}&month={month}&year={year}"
        req = urllib.request.Request(url_city, headers={"User-Agent": "EzanVakti-Linux/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=4) as res:
                if res.status == 200:
                    payload = json.loads(res.read().decode())
                    data_list = payload.get("data", [])
                    if data_list:
                        return data_list
        except Exception:
            pass

        # 2. Coordinate fallback (essential for Turkish districts and towns like Abdipaşa)
        try:
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_city}&count=1&language=tr&format=json"
            geo_req = urllib.request.Request(geo_url, headers={"User-Agent": "EzanHavaApp/1.0"})
            with urllib.request.urlopen(geo_req, timeout=4) as geo_res:
                if geo_res.status == 200:
                    geo_data = json.loads(geo_res.read().decode())
                    results = geo_data.get("results")
                    if results:
                        lat = results[0]["latitude"]
                        lon = results[0]["longitude"]
                        coord_url = f"https://api.aladhan.com/v1/calendar?latitude={lat}&longitude={lon}&method={method}&month={month}&year={year}"
                        coord_req = urllib.request.Request(coord_url, headers={"User-Agent": "EzanVakti-Linux/1.0"})
                        with urllib.request.urlopen(coord_req, timeout=5) as coord_res:
                            if coord_res.status == 200:
                                payload = json.loads(coord_res.read().decode())
                                return payload.get("data", [])
        except Exception as e:
            print(f"Koordinat bazlı takvim çekme hatası ({city}): {e}")

        return None

    def fetch_monthly_calendar(self, city: str, country: str, year: int, month: int) -> bool:
        """Fetches an entire month of timings and saves to SQLite and RAM cache."""
        cache_month_key = (city.lower(), country.lower(), year, month)
        failed_until = self._failed_months.get(cache_month_key)
        if failed_until and datetime.datetime.now() < failed_until:
            return False

        data_list = self._fetch_calendar_payload(city, country, year, month)
        if not data_list:
            self._failed_months[cache_month_key] = datetime.datetime.now() + datetime.timedelta(minutes=5)
            return False

        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            for item in data_list:
                date_info = item.get("date", {})
                gregorian_date = date_info.get("gregorian", {})
                date_str = gregorian_date.get("date")
                
                timings = item.get("timings", {})
                clean = lambda s: s.split()[0] if s else ""
                fajr = clean(timings.get("Fajr"))
                sunrise = clean(timings.get("Sunrise"))
                dhuhr = clean(timings.get("Dhuhr"))
                asr = clean(timings.get("Asr"))
                maghrib = clean(timings.get("Maghrib"))
                isha = clean(timings.get("Isha"))

                hijri = date_info.get("hijri", {})
                hijri_day = hijri.get("day", "")
                hijri_month = hijri.get("month", {}).get("number", 1)
                hijri_year = hijri.get("year", "")

                cur.execute("""
                    INSERT OR REPLACE INTO prayer_cache 
                    (city, country, date_str, fajr, sunrise, dhuhr, asr, maghrib, isha, hijri_day, hijri_month, hijri_year)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (city.lower(), country.lower(), date_str, fajr, sunrise, dhuhr, asr, maghrib, isha, hijri_day, hijri_month, hijri_year))

                # Immediately populate in-memory RAM cache for all 31 days
                h_month_num = hijri_month if hijri_month else 1
                h_month_name = HIJRI_MONTHS_TR.get(h_month_num, "")
                try:
                    parts = [int(p) for p in date_str.split("-")]
                    d_obj = datetime.date(parts[2], parts[1], parts[0])
                    mem_k = (city.lower(), country.lower(), date_str)
                    self._mem_cache[mem_k] = {
                        "date": d_obj,
                        "date_str": date_str,
                        "fajr": fajr,
                        "sunrise": sunrise,
                        "dhuhr": dhuhr,
                        "asr": asr,
                        "maghrib": maghrib,
                        "isha": isha,
                        "hijri_day": hijri_day,
                        "hijri_month": h_month_num,
                        "hijri_month_name": h_month_name,
                        "hijri_year": hijri_year,
                        "hijri_formatted": f"{hijri_day} {h_month_name} {hijri_year}"
                    }
                except Exception:
                    pass

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Veritabanı kaydetme hatası: {e}")
            return False

    def get_day_timings(self, target_date: datetime.date, city: str = None, country: str = None) -> Optional[Dict[str, Any]]:
        """Gets timings for a specific day with 0ms in-memory caching."""
        if not city:
            city = self.settings.get("city", "Darica")
        if not country:
            country = self.settings.get("country", "Turkey")

        date_str = target_date.strftime("%d-%m-%Y")
        city_lower = city.lower()
        country_lower = country.lower()
        cache_key = (city_lower, country_lower, date_str)

        # 1. Check in-memory RAM cache first (0 ms)
        if cache_key in self._mem_cache:
            return self._mem_cache[cache_key]

        # 1b. Recently failed lookup for this city -> serve fallback without touching disk/network
        fb_until = self._fallback_until.get((city_lower, country_lower))
        if fb_until and datetime.datetime.now() < fb_until:
            return self._fallback_timings(target_date)

        # 2. Check SQLite DB
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT fajr, sunrise, dhuhr, asr, maghrib, isha, hijri_day, hijri_month, hijri_year
            FROM prayer_cache
            WHERE city=? AND country=? AND date_str=?
        """, (city_lower, country_lower, date_str))
        row = cur.fetchone()
        conn.close()

        if row:
            h_month_num = row[7] if row[7] else 1
            h_month_name = HIJRI_MONTHS_TR.get(h_month_num, "")
            res = {
                "date": target_date,
                "date_str": date_str,
                "fajr": row[0],
                "sunrise": row[1],
                "dhuhr": row[2],
                "asr": row[3],
                "maghrib": row[4],
                "isha": row[5],
                "hijri_day": row[6],
                "hijri_month": h_month_num,
                "hijri_month_name": h_month_name,
                "hijri_year": row[8],
                "hijri_formatted": f"{row[6]} {h_month_name} {row[8]}"
            }
            self._mem_cache[cache_key] = res
            return res

        # 3. If missing, fetch month once
        success = self.fetch_monthly_calendar(city, country, target_date.year, target_date.month)
        if success:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("""
                SELECT fajr, sunrise, dhuhr, asr, maghrib, isha, hijri_day, hijri_month, hijri_year
                FROM prayer_cache
                WHERE city=? AND country=? AND date_str=?
            """, (city_lower, country_lower, date_str))
            row = cur.fetchone()
            conn.close()
            if row:
                h_month_num = row[7] if row[7] else 1
                h_month_name = HIJRI_MONTHS_TR.get(h_month_num, "")
                res = {
                    "date": target_date,
                    "date_str": date_str,
                    "fajr": row[0],
                    "sunrise": row[1],
                    "dhuhr": row[2],
                    "asr": row[3],
                    "maghrib": row[4],
                    "isha": row[5],
                    "hijri_day": row[6],
                    "hijri_month": h_month_num,
                    "hijri_month_name": h_month_name,
                    "hijri_year": row[8],
                    "hijri_formatted": f"{row[6]} {h_month_name} {row[8]}"
                }
                self._mem_cache[cache_key] = res
                return res

        res = self._fallback_timings(target_date)
        self._fallback_until[(city_lower, country_lower)] = datetime.datetime.now() + datetime.timedelta(minutes=5)
        return res

    def _fallback_timings(self, target_date: datetime.date) -> Dict[str, Any]:
        return {
            "date": target_date,
            "date_str": target_date.strftime("%d-%m-%Y"),
            "fajr": "05:43",
            "sunrise": "07:08",
            "dhuhr": "12:53",
            "asr": "15:57",
            "maghrib": "18:28",
            "isha": "19:47",
            "hijri_day": "5",
            "hijri_month": 5,
            "hijri_month_name": "Cemaziyelevvel",
            "hijri_year": "1448",
            "hijri_formatted": "5 Cemaziyelevvel 1448"
        }

    def get_current_and_next_prayer(self, now: Optional[datetime.datetime] = None) -> Dict[str, Any]:
        if now is None:
            now = datetime.datetime.now()

        today = now.date()
        today_data = self.get_day_timings(today)
        tomorrow_data = self.get_day_timings(today + datetime.timedelta(days=1))
        yesterday_data = self.get_day_timings(today - datetime.timedelta(days=1))

        def to_dt(d: datetime.date, time_str: str) -> datetime.datetime:
            parts = time_str.split(":")
            return datetime.datetime(d.year, d.month, d.day, int(parts[0]), int(parts[1]), 0)

        prayers_dt = []
        for p_key in PRAYER_ORDER:
            dt = to_dt(today, today_data[p_key.lower()])
            prayers_dt.append((p_key, dt))

        if now < prayers_dt[0][1]:
            current_prayer_key = "Isha"
            current_prayer_start = to_dt(yesterday_data["date"], yesterday_data["isha"])
            next_prayer_key = "Fajr"
            next_prayer_time = prayers_dt[0][1]
        elif now >= prayers_dt[-1][1]:
            current_prayer_key = "Isha"
            current_prayer_start = prayers_dt[-1][1]
            next_prayer_key = "Fajr"
            next_prayer_time = to_dt(tomorrow_data["date"], tomorrow_data["fajr"])
        else:
            current_prayer_key = "Isha"
            current_prayer_start = prayers_dt[0][1]
            next_prayer_key = "Fajr"
            next_prayer_time = prayers_dt[1][1]
            for i in range(len(prayers_dt) - 1):
                if prayers_dt[i][1] <= now < prayers_dt[i+1][1]:
                    current_prayer_key = prayers_dt[i][0]
                    current_prayer_start = prayers_dt[i][1]
                    next_prayer_key = prayers_dt[i+1][0]
                    next_prayer_time = prayers_dt[i+1][1]
                    break

        remaining_seconds = max(0, int((next_prayer_time - now).total_seconds()))
        hours, rem = divmod(remaining_seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        countdown_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        total_interval = (next_prayer_time - current_prayer_start).total_seconds()
        elapsed = (now - current_prayer_start).total_seconds()
        progress = max(0.0, min(1.0, elapsed / total_interval)) if total_interval > 0 else 0.0

        sunrise_dt = to_dt(today, today_data["sunrise"])
        dhuhr_dt = to_dt(today, today_data["dhuhr"])
        maghrib_dt = to_dt(today, today_data["maghrib"])

        kerahat_status = None
        if sunrise_dt <= now <= sunrise_dt + datetime.timedelta(minutes=45):
            kerahat_status = "Kerahat Vakti (Güneş Doğuşu +45 dk)"
        elif dhuhr_dt - datetime.timedelta(minutes=45) <= now < dhuhr_dt:
            kerahat_status = "Kerahat Vakti (Zeval Vakti)"
        elif maghrib_dt - datetime.timedelta(minutes=45) <= now < maghrib_dt:
            kerahat_status = "Kerahat Vakti (Güneş Batarken)"

        return {
            "today_timings": today_data,
            "current_prayer_key": current_prayer_key,
            "current_prayer_name": PRAYER_NAMES_TR[current_prayer_key],
            "next_prayer_key": next_prayer_key,
            "next_prayer_name": PRAYER_NAMES_TR[next_prayer_key],
            "next_prayer_time": next_prayer_time.strftime("%H:%M"),
            "remaining_seconds": remaining_seconds,
            "countdown_str": countdown_str,
            "progress": progress,
            "kerahat_status": kerahat_status
        }
