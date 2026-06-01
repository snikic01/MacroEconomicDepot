from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    GEMINI_API_KEY: str = ""
    FRED_API_KEY: str = "" 

    model_config = SettingsConfigDict(env_file=".env")

# Kreiramo instancu klase koju database.py uvozi
settings = Settings()
