import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

class Settings:
    ENVIRONMENT: str = os.getenv("ENVIRONMENT")
    PORT: int = int(os.getenv("PORT") )
    DB_HOST: str = os.getenv("DB_HOST")
    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD: str = quote_plus(os.getenv("DB_PASSWORD"))
    DB_NAME: str = os.getenv("DB_NAME")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")

settings = Settings()
