import time
import logging

from fastapi import APIRouter, Request

from db.connection import get_db
from llm.client import get_client
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
        conn.execute("SELECT COUNT(*) FROM sales_order_headers")
        db_ms = round((time.time() - t) * 1000, 2)
        db_ok = True
    except Exception:
        logger.exception("db health check failed")

    database = StatusService(name="Database (SQLite)", ok=db_ok, latency_ms=db_ms)

    # check LLM — one-token call to OpenRouter
    llm_ok = False
    llm_ms = 0.0
    try:
        t = time.time()
        client = get_client()
        client.chat.completions.create(
            model="nvidia/nemotron-3-super-120b-a12b:free",
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
        )
        llm_ms = round((time.time() - t) * 1000, 2)
        llm_ok = True
    except Exception:
        logger.exception("llm health check failed")

    llm = StatusService(name="LLM (OpenRouter)", ok=llm_ok, latency_ms=llm_ms)

    return StatusResponse(backend=backend, database=database, llm=llm)
