import time
import logging

from fastapi import APIRouter, Request

from db.connection import get_db
from llm.client import get_model, settings
from middleware.rate_limit import limiter
from models.schemas import StatusResponse, StatusService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["status"])


@router.get("/status", response_model=StatusResponse)
@limiter.limit("60/minute")
async def status(request: Request):
    """Health check: backend, SQLite, and LLM status with latency."""
    # backend is always ok if we got this far
    backend = StatusService(name="Backend (FastAPI)", ok=True, latency_ms=0.0)

    # check DB
    db_ok = False
    db_ms = 0.0
    try:
        t = time.time()
        conn = get_db()
        conn.execute("SELECT 1")
        db_ms = round((time.time() - t) * 1000, 2)
        db_ok = True
    except Exception:
        logger.exception("db health check failed")

    database = StatusService(name="Database (SQLite)", ok=db_ok, latency_ms=db_ms)

    # check LLM — simple latency test using Google SDK
    llm_ok = False
    llm_ms = 0.0
    try:
        if settings.gemini_api_key:
            t = time.time()
            model = get_model()
            # use a tiny token generation as a ping
            await model.generate_content_async("ping", generation_config={"max_output_tokens": 1})
            llm_ms = round((time.time() - t) * 1000, 2)
            llm_ok = True
    except Exception:
        logger.exception("llm health check failed")

    llm = StatusService(name="LLM (Gemini 1.5 Flash)", ok=llm_ok, latency_ms=llm_ms)

    return StatusResponse(backend=backend, database=database, llm=llm)
