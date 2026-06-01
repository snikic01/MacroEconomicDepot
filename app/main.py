from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import db
from app.routers import market, economics

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    yield
    await db.disconnect()

app = FastAPI(title="MEDepot API Dashboard", lifespan=lifespan)

# Registracija rutera za finansijske podatke
app.include_router(market.router)
app.include_router(economics.router)

@app.get("/")
async def root():
    return {"status": "online", "message": "MEDepot API radi stabilno!"}
