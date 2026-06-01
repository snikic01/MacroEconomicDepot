from fastapi import APIRouter, HTTPException
import yfinance as yf
from app.database import db

router = APIRouter(prefix="/market", tags=["Market Data"])

# Mapa tikera koje pratimo
TICKERS = {
    "^GSPC": "S&P 500",
    "^IXIC": "Nasdaq",
    "^VIX": "VIX Index",
    "GC=F": "Gold",
    "SI=F": "Silver",
    "CL=F": "Crude Oil"
}

@router.post("/fetch-prices")
async def fetch_and_store_prices():
    """
    Povlači najnovije cene sa Yahoo Finance i upisuje ih u PostgreSQL.
    """
    if not db.pool:
        raise HTTPException(status_code=500, detail="Baza podataka nije povezana.")

    try:
        # 1. Povlačenje podataka sa yfinance (uzimamo zadnji dan sa intervalom od 15m)
        ticker_symbols = list(TICKERS.keys())
        data = yf.download(ticker_symbols, period="1d", interval="15m")

        if data.empty:
            raise HTTPException(status_code=400, detail="Nije moguće povući podatke sa Yahoo Finance.")

        records_to_insert = []
        
        # 2. Parsiranje podataka iz Pandas DataFrame-a
        for ticker in ticker_symbols:
            try:
                # Uzimamo poslednju dostupnu cenu zatvaranja (Close)
                latest_price = data['Close'][ticker].dropna().iloc[-1]
                records_to_insert.append((ticker, float(latest_price)))
            except Exception:
                # Preskačemo tiker ako trenutno nema podataka (npr. vikend ili zatvoreno tržište)
                continue

        if not records_to_insert:
            return {"message": "Tržišta su verovatno zatvorena, nema novih podataka."}

        # 3. Upis u bazu preko ČISTOG SQL-a pomoću asyncpg executemany (masovni brz upis)
        query = """
            INSERT INTO market_data (ticker, price_close)
            VALUES ($1, $2);
        """
        
        async with db.pool.acquire() as connection:
            await connection.executemany(query, records_to_insert)

        return {
            "status": "success",
            "inserted_records": len(records_to_insert),
            "data": {TICKERS[t]: p for t, p in records_to_insert}
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Greška pri radu sa bazom/API-jem: {str(e)}")

@router.get("/latest")
async def get_latest_prices():
    """
    Vraća poslednje zabeležene cene iz baze za sve tikere.
    """
    query = """
        SELECT DISTINCT ON (ticker) ticker, price_close, timestamp
        FROM market_data
        ORDER BY ticker, timestamp DESC;
    """
    async with db.pool.acquire() as connection:
        rows = await connection.fetch(query)
        
    return [
        {
            "ticker": row["ticker"],
            "name": TICKERS.get(row["ticker"], "Unknown"),
            "price": float(row["price_close"]),
            "timestamp": row["timestamp"]
        }
        for row in rows
    ]
