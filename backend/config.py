from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    openrouter_api_key: str = ""
    db_path: str = str(BASE_DIR / "o2c.db")
    data_dir: str = str(BASE_DIR / "dataset/sap-order-to-cash-dataset/sap-o2c-data")
    allowed_origins: str = "http://localhost:3000,http://localhost:8888"

    class Config:
        env_file = str(BASE_DIR / ".env")

settings = Settings()
