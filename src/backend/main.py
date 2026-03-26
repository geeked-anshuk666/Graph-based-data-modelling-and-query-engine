import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from config import settings
from db.connection import get_db
from db.loader import load_all
from graph.builder import build_graph
from middleware.rate_limit import limiter
from middleware.security_headers import SecurityHeaders
from routers import graph, query, status

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: load data if needed, build graph into memory."""
    data_dir = Path(settings.data_dir)
    db_path = Path(settings.db_path)

    # load JSONL data into SQLite on first run
    load_all(data_dir, db_path)

    # build the in-memory graph
    conn = get_db()
    app.state.graph = build_graph(conn)

    logger.info("app ready")
    yield


app = FastAPI(
    title="SAP O2C Graph Query System",
    description="Interactive graph visualization and natural language query interface for SAP Order-to-Cash data",
    version="0.1.0",
    lifespan=lifespan,
)

# rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# security headers on every response
app.add_middleware(SecurityHeaders)

# CORS — origins from env, not wildcard
origins = [o.strip() for o in settings.allowed_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# register routers
app.include_router(graph.router)
app.include_router(query.router)
app.include_router(status.router)

# serve static frontend files if directory exists (for Docker/Standalone)
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        # API routes are already handled above. Everything else goes to index.html
        if full_path.startswith("api"):
            return None # should have been caught by router
        
        file_path = static_path / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        
        return FileResponse(static_path / "index.html")



@app.get("/")
async def root():
    return {"status": "ok", "docs": "/docs"}
