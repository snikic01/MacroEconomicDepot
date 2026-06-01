from fastapi import APIRouter, HTTPException
from app.config import settings
# Uvoz servisa
from app.services import fed, ecb, nbs

router = APIRouter(prefix="/economics", tags=["Economics & Central Banks"])

@router.post("/fetch-historical-fed-rate")
async def fetch_fed_rate(days: int = 30):
    if not settings.FRED_API_KEY:
        raise HTTPException(status_code=400, detail="FRED API ključ nedostaje.")
    inserted = await fed.fetch_fed_rate_history(days)
    return {"status": "success", "inserted_fed_records": inserted}

@router.post("/fetch-historical-yields")
async def fetch_yields(days: int = 30):
    if not settings.FRED_API_KEY:
        raise HTTPException(status_code=400, detail="FRED API ključ nedostaje.")
    inserted = await fed.fetch_yield_curve_history(days)
    return {"status": "success", "inserted_yield_records": inserted}

@router.post("/fetch-ecb-rate")
async def fetch_ecb():
    rate = await ecb.fetch_ecb_rate()
    return {"status": "success", "current_ecb_rate": rate}

@router.post("/fetch-nbs-rate")
async def fetch_nbs():
    rate = await nbs.fetch_nbs_rate()
    return {"status": "success", "current_nbs_rate": rate}

@router.post("/fetch-all-economics")
async def fetch_all_macro_data(days: int = 30):
    """
    JEDAN ENDPOINT ZA SVE: Poziva sve ekonomske servise odjednom!
    """
    if not settings.FRED_API_KEY:
        raise HTTPException(status_code=400, detail="FRED API ključ nedostaje.")
        
    fed_records = await fed.fetch_fed_rate_history(days)
    yield_records = await fed.fetch_yield_curve_history(days)
    ecb_rate = await ecb.fetch_ecb_rate()
    nbs_rate = await nbs.fetch_nbs_rate()
    
    return {
        "status": "success",
        "fed_records_inserted": fed_records,
        "yield_records_inserted": yield_records,
        "current_ecb_rate": ecb_rate,
        "current_nbs_rate": nbs_rate
    }
