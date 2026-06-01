from fastapi import APIRouter, HTTPException
import requests
from datetime import datetime
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

@router.post("/fetch-historical-yields")
async def fetch_historical_yields(days: int = 30):
    """
    Povlači istorijske podatke za krivu prinosa (2Y, 10Y, 30Y) sa FRED-a za uneti broj dana i puni bazu.
    """
    if not settings.FRED_API_KEY:
        raise HTTPException(status_code=400, detail="FRED API ključ nije podešen.")

    total_inserted = 0
    records_to_insert = []

    for duration, series_id in YIELD_SERIES.items():
        # Uzimamo istoriju sa limitom koji zadajemo kroz parametar 'days'
        url = f"https://stlouisfed.org{series_id}&api_key={settings.FRED_API_KEY}&file_type=json&sort_order=desc&limit={days}"
        try:
            response = requests.get(url).json()
            if "observations" in response:
                for obs in response["observations"]:
                    if obs["value"] == ".":  # FRED nekada šalje tačku za praznik/vikend
                        continue
                    
                    # Konvertujemo FRED datum (YYYY-MM-DD) u Python datetime sa UTC zonom
                    obs_date = datetime.strptime(obs["date"], "%Y-%m-%d")
                    value = float(obs["value"])
                    records_to_insert.append((duration, value, obs_date))
        except Exception:
            continue

    if not records_to_insert:
        raise HTTPException(status_code=500, detail="Nije uspelo povlačenje istorijskih prinosa.")

    # Čist SQL INSERT sa eksplicitnim datumom iz FRED-a
    query = """
        INSERT INTO yield_curve (duration, yield_rate, timestamp) 
        VALUES ($1, $2, $3);
    """
    async with db.pool.acquire() as connection:
        await connection.executemany(query, records_to_insert)

    return {"status": "success", "inserted_yield_records": len(records_to_insert)}


@router.post("/fetch-historical-fed-rate")
async def fetch_historical_fed_rate(days: int = 30):
    """
    Povlači istorijske podatke o kamatnoj stopi FED-a i dodaje nove redove u bazu za istorijski grafikon.
    """
    if not settings.FRED_API_KEY:
        raise HTTPException(status_code=400, detail="FRED API ključ nije podešen.")

    url = f"https://stlouisfed.org{FED_RATE_SERIES}&api_key={settings.FRED_API_KEY}&file_type=json&sort_order=desc&limit={days}"
    
    records_to_insert = []
    try:
        response = requests.get(url).json()
        if "observations" in response:
            for obs in response["observations"]:
                if obs["value"] == ".":
                    continue
                
                obs_date = datetime.strptime(obs["date"], "%Y-%m-%d")
                rate = float(obs["value"])
                
                # Zapisujemo istorijski presek u bazu
                records_to_insert.append(('FED', 'Federal Reserve (USA)', rate, obs_date))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Greška pri radu sa FRED-om: {str(e)}")

    if not records_to_insert:
        raise HTTPException(status_code=400, detail="Nema podataka za upis.")

    # ISPRAVKA: Radimo INSERT umesto UPDATE-a i punimo tabelu istorijom!
    query = """
        INSERT INTO central_banks (bank_code, bank_name, interest_rate, last_updated)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (bank_code, last_updated) DO NOTHING; 
    """
    # NAPOMENA: Da bi ON CONFLICT radio, moramo dodati jedinstveni indeks u bazu (vidi Korak 2)
    
    async with db.pool.acquire() as connection:
        await connection.executemany(query, records_to_insert)

    return {"status": "success", "inserted_fed_records": len(records_to_insert)}
