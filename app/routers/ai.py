import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import APIRouter, HTTPException
from google import genai
from app.config import settings
from app.database import db

router = APIRouter(prefix="/ai", tags=["Gemini AI Analytics"])

@router.get("/macro-intelligence-report")
async def generate_macro_report():
    """
    Povlači najnovije ekonomske i tržišne podatke iz PostgreSQL baze i šalje ih Gemini AI na analizu.
    """
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=400, detail="Gemini API ključ nije podešen u .env fajlu.")

    if not db.pool:
        raise HTTPException(status_code=500, detail="Baza podataka nije povezana.")

    try:
        # 1. Povlačenje najnovijih cena za ključne indekse i sirovine
        market_query = """
            SELECT DISTINCT ON (ticker) ticker, price_close 
            FROM market_data 
            WHERE ticker IN ('^GSPC', '^IXIC', '^VIX', 'GC=F', 'CL=F')
            ORDER BY ticker, timestamp DESC;
        """
        
        # 2. Povlačenje najnovijeg stanja američke krive prinosa
        yield_query = """
            SELECT duration, yield_rate 
            FROM yield_curve 
            WHERE id IN (
                SELECT MAX(id) FROM yield_curve GROUP BY duration
            );
        """
        
        # 3. Povlačenje trenutnih kamatnih stopa centralnih banaka
        banks_query = """
            SELECT bank_code, bank_name, interest_rate 
            FROM central_banks;
        """
        
        # 4. Povlačenje poslednja dva zapisa za sentiment (Traditional i Crypto)
        fng_query = """
            SELECT index_value, sentiment 
            FROM fear_greed_index 
            ORDER BY timestamp DESC 
            LIMIT 2;
        """

        async with db.pool.acquire() as connection:
            market_rows = await connection.fetch(market_query)
            yield_rows = await connection.fetch(yield_query)
            bank_rows = await connection.fetch(banks_query)
            fng_rows = await connection.fetch(fng_query)

        # 5. Formatiranje prikupljenih podataka u tekst za AI prompt
        market_text = "\n".join([f"- {row['ticker']}: {float(row['price_close']):.2f}" for row in market_rows])
        yield_text = "\n".join([f"- SAD {row['duration']} Prinos: {float(row['yield_rate'])}%" for row in yield_rows])
        banks_text = "\n".join([f"- {row['bank_code']} ({row['bank_name']}): {float(row['interest_rate'])}%" for row in bank_rows])
        
        fng_text_list = []
        for row in fng_rows:
            fng_text_list.append(f"- {row['sentiment']}: {row['index_value']}/100")
        fng_text = "\n".join(fng_text_list) if fng_text_list else "Nema podataka"

        # 6. Formulisanje naprednog prompta za Gemini 1.5 Flash
        prompt = f"""
        Ti si elitni makroekonomski strateg, kvantitativni analitičar i savetnik za investicione fondove.
        Dobio si direktan presek sirovih finansijskih i ekonomskih podataka iz našeg centralnog skladišta (MEDepot):

        🏛️ MONETARNA POLITIKA (KAMATNE STOPE CENTRALNIH BANKA):
        {banks_text}

        📈 KLJUČNI GLOBALNI INDEKSI I ROBA:
        {market_text}

        📊 AMERIČKA KRIVA PRINOSA (USA YIELD CURVE):
        {yield_text}

        🧠 PSIHOLOGIJA I SENTIMENT TRŽIŠTA:
        {fng_text}

        Zadatak: Napravi sveobuhvatan, dubok i visoko profesionalan makroekonomski izveštaj na SRPSKOM jeziku.
        Izveštaj mora imati sledeću jasnu strukturu sa Markdown naslovima:

        ## 1. Globalni Monetarni Pejzaž
        ## 2. Dinamika Tržišta i Tokovi Kapitala
        ## 3. Kriva Prinosa i Recesiona Upozorenja
        ## 4. Analiza Sentiment i Tržišna Psihologija
        ## 5. Strateške Preporuke za Portfolio Menadžere
        """

        # 7. Pozivanje Google GenAI SDK klijenta
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )

        return {
            "status": "success",
            "model_used": "gemini-2.5-flash",
            "report": response.text
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Greška tokom generisanja AI izveštaja: {str(e)}")
