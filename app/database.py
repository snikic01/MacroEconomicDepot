import asyncpg
from app.config import settings

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        # Otvara bazen konekcija kada se server pokrene
        self.pool = await asyncpg.create_pool(settings.DATABASE_URL)
        print("O Uspešno povezan sa MEDepot_db bazom preko asyncpg-a!")

    async def disconnect(self):
        # Zatvara sve otvorene konekcije kada se aplikacija ugasi
        if self.pool:
            await self.pool.close()
            print("X Konekcija sa bazom je zatvorena.")

# Kreiramo instancu klase koju main.py uvozi
db = Database()
