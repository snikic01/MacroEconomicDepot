import requests
from datetime import datetime
from app.config import settings
from app.database import db

FED_RATE_SERIES = "FEDFUNDS"
YIELD_SERIES = {"2Y": "GS2", "10Y": "GS10", "30Y": "GS30"}

async def fetch_fed_rate_history(days: int):
    url = f"https://stlouisfed.org{FED_RATE_SERIES}&api_key={settings.FRED_API_KEY}&file_type=json&sort_order=desc&limit={days}"
    records = []
    
    try:
        response = requests.get(url, timeout=10).json()
        if "observations" in response:
            for obs in response["observations"]:
                try:
                    if obs["value"] == ".": 
                        continue
                    obs_date = datetime.strptime(obs["date"], "%Y-%m-%d")
                    rate_value = float(obs["value"])
                    records.append(('FED', 'Federal Reserve (USA)', rate_value, obs_date))
                except (ValueError, KeyError):
                    continue
    except Exception as e:
        print(f"⚠️ FED Rate Servis Greška: {str(e)}")
        pass

    if records:
        query = """
            INSERT INTO central_banks (bank_code, bank_name, interest_rate, last_updated)
            VALUES ($1, $2, $3, $4) 
            ON CONFLICT (bank_code, last_updated) DO NOTHING;
        """
        async with db.pool.acquire() as conn:
            await conn.executemany(query, records)
    return len(records)

async def fetch_yield_curve_history(days: int):
    records = []
    
    for duration, series_id in YIELD_SERIES.items():
        url = f"https://stlouisfed.org{series_id}&api_key={settings.FRED_API_KEY}&file_type=json&sort_order=desc&limit={days}"
        try:
            response = requests.get(url, timeout=10).json()
            if "observations" in response:
                for obs in response["observations"]:
                    try:
                        if obs["value"] == ".": 
                            continue
                        obs_date = datetime.strptime(obs["date"], "%Y-%m-%d")
                        yield_value = float(obs["value"])
                        records.append((duration, yield_value, obs_date))
                    except (ValueError, KeyError):
                        continue
        except Exception as e:
            print(f"⚠️ Yield Curve Servis Greška za {duration}: {str(e)}")
            continue
            
    if records:
        query = "INSERT INTO yield_curve (duration, yield_rate, timestamp) VALUES ($1, $2, $3);"
        async with db.pool.acquire() as conn:
            await conn.executemany(query, records)
    return len(records)
