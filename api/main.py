from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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

# Handle CORS manually for all requests
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    if request.method == "OPTIONS":
        response = Response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Max-Age"] = "86400"
        return response
    
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Keep the middleware too for redundancy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reports.router)
app.include_router(search.router)
app.include_router(analytics.router)
app.include_router(pipeline.router)


@app.get("/", tags=["root"])
def root():
    return {"name": "Signal API", "version": "0.1.0", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse, tags=["root"])
def health_check():
    h = check_health()
    return HealthResponse(
        status="ok" if all([h["postgres"], h["qdrant"], h["duckdb"]]) else "degraded",
        **h,
    )


@app.on_event("startup")
async def startup():
    logger.info("Signal API starting up...")
    logger.info("API ready — models will load on first request")