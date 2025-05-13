import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OPENAPI_KEY: str = os.getenv("OPENAPI_KEY", "")
    OPENROUTER_KEY: str = os.getenv("OPENROUTER_KEY", "")
    PROXY_URL: str = os.getenv("PROXY_URL", "http://localhost:9090")

settings = Settings()
