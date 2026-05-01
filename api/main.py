"""
Main FastAPI application for PiGenus orchestration node.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from api.endpoints import health, auth, workers, jobs, memory, admin
from api.middleware import setup_middleware, logging_middleware, error_middleware
from core.config import settings
from db.database import engine
from db.models import SQLModel
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Create database tables (only in development)
def create_db_and_tables():
    if settings.debug:
        SQLModel.metadata.create_all(engine)
        logger.info("Database tables created (development mode)")


# Create FastAPI app
app = FastAPI(
    title="PiGenus",
    description="Private orchestration node for the GENUS ecosystem",
    version="0.1.0",
    debug=settings.debug,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware (adjust in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup custom middleware
setup_middleware(app)

# Include API routers
app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(workers.router, prefix="/workers", tags=["workers"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(memory.router, prefix="/memory", tags=["memory"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])


# Global exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Startup event
@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    logger.info("PiGenus API started")


# Shutdown event
@app.on_event("shutdown")
def on_shutdown():
    logger.info("PiGenus API shutting down")


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    return {
        "message": "PiGenus - Private Orchestration Node",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
