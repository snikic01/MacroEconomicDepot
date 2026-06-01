import requests
import re
import xml.etree.ElementTree as ET
from app.database import db

async def fetch_ecb_rate():
    url = "https://europa.eu"
    latest_rate = 4.00
    try:
        response = requests.get(url)
        root = ET.fromstring(response.content)
        description_text = root.find(".//item/description").text
        rates = re.findall(r"\d+\.\d+", description_text)
        if rates: latest_rate = float(rates[0])
    except Exception:
        pass

    query = """
        INSERT INTO central_banks (bank_code, bank_name, interest_rate, last_updated)
        VALUES ('ECB', 'European Central Bank (EU)', $1, NOW()) ON CONFLICT (bank_code, last_updated) DO NOTHING;
    """
    async with db.pool.acquire() as conn:
        await conn.execute(query, latest_rate)
    return latest_rate
