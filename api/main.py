"""
Main FastAPI application for PiGenus orchestration node.

PiGenus ist der dauerhaft verfügbare, private Infrastruktur-Kern des GENUS-Systems.
Er erfüllt fünf Grundfunktionen:
1. Persistenz: Bewahrt Zustände über Zeit.
2. Orchestrierung: Verteilt Arbeit intelligent an geeignete Ressourcen.
3. Administration: Verwaltet das Gesamtsystem.
4. Schnittstellenfähigkeit: Verbindet unterschiedliche Geräte, Dienste und Instanzen.
5. Kontinuität: Läuft dauerhaft, verlässlich und ressourcenschonend.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from api.endpoints import health, auth, workers, jobs, memory, admin
from api.middleware import setup_middleware, logging_middleware, error_middleware
from core.config import settings
from core.philosophy import PiGenusPrinciple
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
    description=(
        "PiGenus ist der dauerhaft verfügbare, private Infrastruktur-Kern des GENUS-Systems. "
        "Er erfüllt fünf Grundfunktionen: Persistenz, Orchestrierung, Administration, "
        "Schnittstellenfähigkeit und Kontinuität."
    ),
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

# Include API routers with philosophy tags
app.include_router(
    health.router,
    tags=["health", PiGenusPrinciple.CONTINUITY.value]
)
app.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth", PiGenusPrinciple.ADMINISTRATION.value]
)
app.include_router(
    workers.router,
    prefix="/workers",
    tags=["workers", PiGenusPrinciple.ORCHESTRATION.value, PiGenusPrinciple.ADMINISTRATION.value]
)
app.include_router(
    jobs.router,
    prefix="/jobs",
    tags=["jobs", PiGenusPrinciple.ORCHESTRATION.value]
)
app.include_router(
    memory.router,
    prefix="/memory",
    tags=["memory", PiGenusPrinciple.PERSISTENCE.value]
)
app.include_router(
    admin.router,
    prefix="/admin",
    tags=["admin", PiGenusPrinciple.ADMINISTRATION.value, PiGenusPrinciple.CONTINUITY.value]
)


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
    logger.info("PiGenus API started (KONTINUITÄT: 24/7-Betrieb bereit)")


# Shutdown event
@app.on_event("shutdown")
def on_shutdown():
    logger.info("PiGenus API shutting down")


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    return {
        "message": "PiGenus - Dauerhaft verfügbarer Infrastruktur-Kern des GENUS-Systems",
        "version": "0.1.0",
        "philosophy": {
            "persistenz": "Bewahrt Zustände über Zeit",
            "orchestrierung": "Verteilt Arbeit intelligent an Ressourcen",
            "administration": "Verwaltet das Gesamtsystem",
            "schnittstellenfaehigkeit": "Verbindet Geräte, Dienste und Instanzen",
            "kontinuität": "Läuft dauerhaft, verlässlich und ressourcenschonend"
        },
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
