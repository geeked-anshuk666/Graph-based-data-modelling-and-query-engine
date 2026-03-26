import time
import logging

from fastapi import APIRouter, Request
from google.api_core.exceptions import ResourceExhausted

from db.connection import get_db
from llm.client import get_model, settings, retry_gemini
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

    # check LLM — simple latency test using Google SDK + retry resilience
    llm_ok = False
    llm_ms = 0.0
    try:
        if settings.gemini_api_key:
            t = time.time()
            # perform the check inside a local lambda so we can apply retry logic
            @retry_gemini
            async def check_llm():
                model = get_model()
                await model.generate_content_async("ping", generation_config={"max_output_tokens": 1})
            
            await check_llm()
            llm_ms = round((time.time() - t) * 1000, 2)
            llm_ok = True
    except ResourceExhausted:
        logger.warning("Status check failed: Rate limit exhausted")
        # we consider it "ok" but with high latency or marked as rate-limited 
        # for now, just mark as failed to show status
        llm_ok = False 
    except Exception:
        logger.exception("llm health check failed")

    llm = StatusService(name="LLM (Gemini 2.5 Flash)", ok=llm_ok, latency_ms=llm_ms)

    return StatusResponse(backend=backend, database=database, llm=llm)
