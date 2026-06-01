import requests
import re
import xml.etree.ElementTree as ET
from app.database import db

async def fetch_ecb_rate():
    url = "https://europa.eu"
    latest_rate = 4.00  # Defaultna/Fallback vrednost ako RSS struktura zakaže
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            description_element = root.find(".//item/description")
            if description_element is not None and description_element.text:
                description_text = description_element.text
                rates = re.findall(r"\d+\.\d+", description_text)
                if rates: 
                    latest_rate = float(rates[0])  # ISPRAVKA: Uzimamo prvi pronađeni broj iz liste
    except Exception as e:
        print(f" ECB Servis Fallback aktiviran zbog: {str(e)}")
        pass

    query = """
        INSERT INTO central_banks (bank_code, bank_name, interest_rate, last_updated)
        VALUES ('ECB', 'European Central Bank (EU)', $1, NOW()) 
        ON CONFLICT (bank_code, last_updated) DO NOTHING;
    """
    async with db.pool.acquire() as conn:
        await conn.execute(query, latest_rate)
    return latest_rate
