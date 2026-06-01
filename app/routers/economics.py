from fastapi import APIRouter, HTTPException
import requests
from app.config import settings
from app.database import db

router = APIRouter(prefix="/economics", tags=["Economics & Central Banks"])

# FRED kodovi za 2Y, 10Y i 30Y prinose obveznica i FED stopu
YIELD_SERIES = {
    "2Y": "GS2",
    "10Y": "GS10",
    "30Y": "GS30"
}
FED_RATE_SERIES = "FEDFUNDS"

@router.post("/fetch-yield-curve")
async def fetch_and_store_yield_curve():
    """
    Povlači najnovije prinose (2Y, 10Y, 30Y) sa FRED-a i upisuje u PostgreSQL.
    """
    if not settings.FRED_API_KEY:
        raise HTTPException(status_code=400, detail="FRED API ključ nije podešen u .env fajlu.")

    records_to_insert = []
    
    for duration, series_id in YIELD_SERIES.items():
        url = f"https://stlouisfed.org{series_id}&api_key={settings.FRED_API_KEY}&file_type=json&sort_order=desc&limit=1"
        try:
            response = requests.get(url).json()
            latest_observation = response["observations"][0]
            value = float(latest_observation["value"])
            records_to_insert.append((duration, value))
        except Exception:
            continue

    if not records_to_insert:
        raise HTTPException(status_code=500, detail="Nije uspelo povlačenje podataka sa FRED API-ja.")

    # Upis u tabelu yield_curve
    query = "INSERT INTO yield_curve (duration, yield_rate) VALUES ($1, $2);"
    async with db.pool.acquire() as connection:
        await connection.executemany(query, records_to_insert)

    return {"status": "success", "inserted_yields": {d: v for d, v in records_to_insert}}


@router.post("/fetch-fed-rate")
async def fetch_and_store_fed_rate():
    """
    Povlači efektivnu kamatnu stopu FED-a i ažurira postojeći red u central_banks.
    """
    if not settings.FRED_API_KEY:
        raise HTTPException(status_code=400, detail="FRED API ključ nije podešen.")

    url = f"https://stlouisfed.org{FED_RATE_SERIES}&api_key={settings.FRED_API_KEY}&file_type=json&sort_order=desc&limit=1"
    
    try:
        response = requests.get(url).json()
        latest_rate = float(response["observations"][0]["value"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Greška pri parsiranju FED stope: {str(e)}")

    # SQL UPDATE za FED red koji smo na početku ubacili u bazu
    query = """
        UPDATE central_banks 
        SET interest_rate = $1, last_updated = NOW() 
        WHERE bank_code = 'FED';
    """
    async with db.pool.acquire() as connection:
        await connection.execute(query, latest_rate)

    return {"status": "success", "current_fed_rate": latest_rate}
