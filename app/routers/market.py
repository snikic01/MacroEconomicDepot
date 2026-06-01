from fastapi import APIRouter, HTTPException
import yfinance as yf
from app.database import db

router = APIRouter(prefix="/market", tags=["Market Data"])

TICKERS = {
    # ==========================================
    # 0. INDEKSI I ROBA (COMMODITIES)
    # ==========================================
    "^GSPC": {"name": "S&P 500", "sector": "Index"},
    "^IXIC": {"name": "Nasdaq", "sector": "Index"},
    "^VIX": {"name": "VIX Index", "sector": "Index"},
    "GC=F": {"name": "Gold", "sector": "Commodity"},
    "SI=F": {"name": "Silver", "sector": "Commodity"},
    "CL=F": {"name": "Crude Oil", "sector": "Commodity"},

    # ==========================================
    # 1. TECHNOLOGY (SAD & EU)
    # ==========================================
    "MSFT": {"name": "Microsoft", "sector": "Technology"},
    "AAPL": {"name": "Apple", "sector": "Technology"},
    "NVDA": {"name": "NVIDIA", "sector": "Technology"},
    "AVGO": {"name": "Broadcom", "sector": "Technology"},
    "ORCL": {"name": "Oracle", "sector": "Technology"},
    "CRM": {"name": "Salesforce", "sector": "Technology"},
    "AMD": {"name": "AMD", "sector": "Technology"},
    "QCOM": {"name": "Qualcomm", "sector": "Technology"},
    "INTC": {"name": "Intel", "sector": "Technology"},
    "ASML": {"name": "ASML Holding", "sector": "Technology"},  # EU
    "SAP": {"name": "SAP SE", "sector": "Technology"},        # EU

    # ==========================================
    # 2. COMMUNICATION SERVICES
    # ==========================================
    "GOOGL": {"name": "Alphabet", "sector": "Communication"},
    "META": {"name": "Meta", "sector": "Communication"},
    "NFLX": {"name": "Netflix", "sector": "Communication"},
    "DIS": {"name": "Walt Disney", "sector": "Communication"},
    "TMUS": {"name": "T-Mobile US", "sector": "Communication"},
    "VZ": {"name": "Verizon", "sector": "Communication"},
    "T": {"name": "AT&T", "sector": "Communication"},
    "VOD.L": {"name": "Vodafone", "sector": "Communication"}, # EU

    # ==========================================
    # 3. CONSUMER CYCLICAL (DISKRECIONA POTROŠNJA)
    # ==========================================
    "AMZN": {"name": "Amazon", "sector": "Consumer Cyclical"},
    "TSLA": {"name": "Tesla", "sector": "Consumer Cyclical"},
    "HD": {"name": "Home Depot", "sector": "Consumer Cyclical"},
    "NKE": {"name": "Nike", "sector": "Consumer Cyclical"},
    "MCD": {"name": "McDonald's", "sector": "Consumer Cyclical"},
    "SBUX": {"name": "Starbucks", "sector": "Consumer Cyclical"},
    "BKNG": {"name": "Booking Holdings", "sector": "Consumer Cyclical"},
    "MC.PA": {"name": "LVMH", "sector": "Consumer Cyclical"},   # EU
    "BMW.DE": {"name": "BMW", "sector": "Consumer Cyclical"},   # EU

    # ==========================================
    # 4. FINANCIALS (BANKARSTVO & OSIGURANJE)
    # ==========================================
    "JPM": {"name": "JPMorgan Chase", "sector": "Financials"},
    "BAC": {"name": "Bank of America", "sector": "Financials"},
    "WFC": {"name": "Wells Fargo", "sector": "Financials"},
    "MS": {"name": "Morgan Stanley", "sector": "Financials"},
    "GS": {"name": "Goldman Sachs", "sector": "Financials"},
    "V": {"name": "Visa", "sector": "Financials"},
    "MA": {"name": "Mastercard", "sector": "Financials"},
    "AXP": {"name": "American Express", "sector": "Financials"},
    "BLK": {"name": "BlackRock", "sector": "Financials"},
    "HSBA.L": {"name": "HSBC", "sector": "Financials"},       # EU
    "GLE.PA": {"name": "Societe Generale", "sector": "Financials"}, # EU

    # ==========================================
    # 5. HEALTHCARE (FARMACIJA & MEDICINA)
    # ==========================================
    "LLY": {"name": "Eli Lilly", "sector": "Healthcare"},
    "UNH": {"name": "UnitedHealth", "sector": "Healthcare"},
    "JNJ": {"name": "Johnson & Johnson", "sector": "Healthcare"},
    "MRK": {"name": "Merck", "sector": "Healthcare"},
    "ABV_E": {"name": "AbbVie", "sector": "Healthcare"},
    "PFE": {"name": "Pfizer", "sector": "Healthcare"},
    "TMO": {"name": "Thermo Fisher", "sector": "Healthcare"},
    "NESN.SW": {"name": "Nestle", "sector": "Healthcare"},    # EU
    "NOVN.SW": {"name": "Novartis", "sector": "Healthcare"},  # EU
    "BAYN.DE": {"name": "Bayer", "sector": "Healthcare"},     # EU

    # ==========================================
    # 6. CONSUMER STAPLES (OSNOVNA POTROŠNJA)
    # ==========================================
    "PG": {"name": "Procter & Gamble", "sector": "Consumer Staples"},
    "KO": {"name": "Coca-Cola", "sector": "Consumer Staples"},
    "PEP": {"name": "PepsiCo", "sector": "Consumer Staples"},
    "WMT": {"name": "Walmart", "sector": "Consumer Staples"},
    "COST": {"name": "Costco", "sector": "Consumer Staples"},
    "PM": {"name": "Philip Morris", "sector": "Consumer Staples"},
    "UL": {"name": "Unilever", "sector": "Consumer Staples"},   # EU

    # ==========================================
    # 7. ENERGY (NAFTA & GAS)
    # ==========================================
    "XOM": {"name": "Exxon Mobil", "sector": "Energy"},
    "CVX": {"name": "Chevron", "sector": "Energy"},
    "COP": {"name": "ConocoPhillips", "sector": "Energy"},
    "SLB": {"name": "Schlumberger", "sector": "Energy"},
    "EOG": {"name": "EOG Resources", "sector": "Energy"},
    "SHEL.L": {"name": "Shell", "sector": "Energy"},          # EU
    "TTE": {"name": "TotalEnergies", "sector": "Energy"},     # EU
    "BP.L": {"name": "BP", "sector": "Energy"},               # EU

    # ==========================================
    # 8. INDUSTRIALS (AERO, TRANSPORT, PROIZVODNJA)
    # ==========================================
    "GE": {"name": "General Electric", "sector": "Industrials"},
    "CAT": {"name": "Caterpillar", "sector": "Industrials"},
    "UNP": {"name": "Union Pacific", "sector": "Industrials"},
    "HON": {"name": "Honeywell", "sector": "Industrials"},
    "LMT": {"name": "Lockheed Martin", "sector": "Industrials"},
    "UPS": {"name": "United Parcel Service", "sector": "Industrials"},
    "BA": {"name": "Boeing", "sector": "Industrials"},
    "SIEGn.DE": {"name": "Siemens", "sector": "Industrials"}, # EU
    "AIR.PA": {"name": "Airbus", "sector": "Industrials"},    # EU

    # ==========================================
    # 9. MATERIALS (SIROVINE, METALI, HEMIJA)
    # ==========================================
    "LIN": {"name": "Linde", "sector": "Materials"},
    "SHW": {"name": "Sherwin-Williams", "sector": "Materials"},
    "FCX": {"name": "Freeport-McMoRan", "sector": "Materials"},
    "ECL": {"name": "Ecolab", "sector": "Materials"},
    "NUE": {"name": "Nucor", "sector": "Materials"},
    "BAS.DE": {"name": "BASF", "sector": "Materials"},         # EU
    "CRH": {"name": "CRH plc", "sector": "Materials"},         # EU

    # ==========================================
    # 10. UTILITIES (STRUJA, VODA, GASNE MREŽE)
    # ==========================================
    "NEE": {"name": "NextEra Energy", "sector": "Utilities"},
    "DUK": {"name": "Duke Energy", "sector": "Utilities"},
    "SO": {"name": "Southern Company", "sector": "Utilities"},
    "CEG": {"name": "Constellation Energy", "sector": "Utilities"},
    "AEP": {"name": "American Electric Power", "sector": "Utilities"},
    "RWE.DE": {"name": "RWE", "sector": "Utilities"},          # EU

    # ==========================================
    # 11. REAL ESTATE (NEKRETNINE)
    # ==========================================
    "PLD": {"name": "Prologis", "sector": "Real Estate"},
    "AMT": {"name": "American Tower", "sector": "Real Estate"},
    "EQIX": {"name": "Equinix", "sector": "Real Estate"},
    "CCI": {"name": "Crown Castle", "sector": "Real Estate"},
    "SPG": {"name": "Simon Property Group", "sector": "Real Estate"},
    "VNA.DE": {"name": "Vonovia", "sector": "Real Estate"}     # EU
}

@router.post("/fetch-prices")
async def fetch_and_store_prices():
    """
    Povlači najnovije cene sa Yahoo Finance i upisuje ih u PostgreSQL.
    """
    if not db.pool:
        raise HTTPException(status_code=500, detail="Baza podataka nije povezana.")

    try:
        ticker_symbols = list(TICKERS.keys())
        # Povlačenje podataka sa yfinance (skupni zahtev za sve tikere)
        data = yf.download(ticker_symbols, period="1d", interval="15m")

        if data.empty:
            raise HTTPException(status_code=400, detail="Nije moguće povući podatke sa Yahoo Finance.")

        records_to_insert = []
        inserted_preview = {}
        
        for ticker in ticker_symbols:
            try:
                # Bezbedno izvlačenje Close cene iz MultiIndex DataFrame-a
                if 'Close' in data.columns:
                    if ticker in data['Close'].columns:
                        series = data['Close'][ticker].dropna()
                        if not series.empty:
                            latest_price = float(series.iloc[-1])
                            records_to_insert.append((ticker, latest_price))
                            inserted_preview[TICKERS[ticker]["name"]] = latest_price
            except Exception:
                continue

        if not records_to_insert:
            return {"message": "Tržišta su zatvorena ili nema novih podataka."}

        # Masovni upis u bazu preko asyncpg
        query = "INSERT INTO market_data (ticker, price_close) VALUES ($1, $2);"
        
        async with db.pool.acquire() as connection:
            await connection.executemany(query, records_to_insert)

        return {
            "status": "success",
            "inserted_records": len(records_to_insert),
            "data": inserted_preview
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Greška pri radu sa bazom/API-jem: {str(e)}")

@router.get("/latest")
async def get_latest_prices():
    """
    Vraća poslednje zabeležene cene iz baze za sve tikere sa pratećim sektorima.
    """
    if not db.pool:
        raise HTTPException(status_code=500, detail="Baza podataka nije povezana.")

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
            "name": TICKERS.get(row["ticker"], {}).get("name", "Unknown"),
            "sector": TICKERS.get(row["ticker"], {}).get("sector", "Unknown"),
            "price": float(row["price_close"]),
            "timestamp": row["timestamp"]
        }
        for row in rows
    ]
