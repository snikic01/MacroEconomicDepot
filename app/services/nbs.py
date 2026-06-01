import requests
import re
from bs4 import BeautifulSoup
from app.database import db

async def fetch_nbs_rate():
    latest_rate = 5.75
    try:
        nbs_html = requests.get("https://nbs.rs", headers={"User-Agent": "Mozilla"}, timeout=10).text
        soup = BeautifulSoup(nbs_html, "html.parser")
        rate_element = soup.find(string=re.compile(r"Referentna kamatna stopa"))
        if rate_element:
            parent = rate_element.find_parent()
            rates = re.findall(r"\d+,\d+|\d+\.\d+", parent.text)
            if rates: latest_rate = float(rates[0].replace(',', '.'))
    except Exception:
        pass

    query = """
        INSERT INTO central_banks (bank_code, bank_name, interest_rate, last_updated)
        VALUES ('NBS', 'Narodna banka Srbije (Srbija)', $1, NOW()) ON CONFLICT (bank_code, last_updated) DO NOTHING;
    """
    async with db.pool.acquire() as conn:
        await conn.execute(query, latest_rate)
    return latest_rate
