from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    openrouter_api_key: str = ""
    gemini_api_key: str = ""
    db_path: str = str(BASE_DIR / "o2c.db")
    data_dir: str = str(BASE_DIR / "dataset/sap-order-to-cash-dataset/sap-o2c-data")
    allowed_origins: str = "http://localhost:3000,http://localhost:8888"

    @field_validator("db_path", "data_dir", mode="before")
    @classmethod
    def make_absolute(cls, v: str) -> str:
        # if path is relative, resolve it against BASE_DIR
        p = Path(v)
        if not p.is_absolute():
            return str((BASE_DIR / p).resolve())
        return str(p.resolve())

    class Config:
        env_file = str(BASE_DIR / ".env")
        extra = "allow"

settings = Settings()
