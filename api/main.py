from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from dotenv import load_dotenv

from api.routes import reports, search, analytics, pipeline
from api.dependencies import check_health
from api.models import HealthResponse

load_dotenv()

app = FastAPI(
    title="Signal API",
    description="Autonomous market intelligence for AI/ML and Fintech",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow Next.js frontend on port 3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(reports.router)
app.include_router(search.router)
app.include_router(analytics.router)
app.include_router(pipeline.router)


@app.get("/", tags=["root"])
def root():
    return {
        "name": "Signal API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["root"])
def health_check():
    """Check health of all downstream systems."""
    h = check_health()
    return HealthResponse(
        status="ok" if all([h["postgres"], h["qdrant"], h["duckdb"]]) else "degraded",
        **h,
    )


@app.on_event("startup")
async def startup():
    logger.info("Signal API starting up...")
    # Don't load heavy models at startup — load lazily on first request
    logger.info("API ready — models will load on first request")