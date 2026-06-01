import requests
import re
from bs4 import BeautifulSoup
from app.database import db

async def fetch_nbs_rate():
    latest_rate = 5.75  # Defaultna/Fallback vrednost ako sajt NBS promeni strukturu
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        nbs_html = requests.get("https://nbs.rs", headers=headers, timeout=10).text
        soup = BeautifulSoup(nbs_html, "html.parser")
        
        # Tražimo tekstualni element na prvoj strani gde NBS drži stopu
        rate_element = soup.find(string=re.compile(r"Referentna kamatna stopa"))
        if rate_element:
            parent = rate_element.find_parent()
            if parent and parent.text:
                # Izvlačimo procente koji mogu biti u formatu 5.75 ili 5,75
                rates = re.findall(r"\d+,\d+|\d+\.\d+", parent.text)
                if rates:
                    clean_rate = rates[0].replace(',', '.')  # Čistimo zareze unutar stringa
                    latest_rate = float(clean_rate)
    except Exception as e:
        print(f"⚠️ NBS Servis Fallback aktiviran zbog: {str(e)}")
        pass

    query = """
        INSERT INTO central_banks (bank_code, bank_name, interest_rate, last_updated)
        VALUES ('NBS', 'Narodna banka Srbije (Srbija)', $1, NOW()) 
        ON CONFLICT (bank_code, last_updated) DO NOTHING;
    """
    async with db.pool.acquire() as conn:
        await conn.execute(query, latest_rate)
    return latest_rate
