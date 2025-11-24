# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging

from app.core.config import settings
from app.core.database import init_db, check_db_connection
from app.api.routes import auth_router, clients_router, activities_router
from app.middleware import LoggingMiddleware, RateLimitMiddleware
from app.services.auth_service import create_initial_admin

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging middleware
app.add_middleware(LoggingMiddleware)

# Rate limiting with higher limits (200 requests per minute)
app.add_middleware(RateLimitMiddleware, requests_per_minute=200)

# HTTPS enforcement
if settings.REQUIRE_HTTPS:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])


@app.on_event("startup")
async def startup_event():
    logger.info(f"🚀 Starting {settings.PROJECT_NAME} API v{settings.API_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    if not check_db_connection():
        logger.error("❌ Failed to connect to database")
        raise RuntimeError("Database connection failed")
    
    logger.info("✅ Database connection successful")
    
    try:
        init_db()
    except Exception as e:
        logger.error(f"❌ DB initialization failed: {e}")
        raise
    
    try:
        create_initial_admin()
    except Exception as e:
        logger.warning(f"⚠️ Initial admin creation: {e}")
    
    logger.info("✅ Application fully started")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 Shutting down application")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": settings.API_VERSION
    }


# API Routes
app.include_router(
    auth_router,
    prefix=f"/api/{settings.API_VERSION}/auth",
    tags=["Authentication"]
)

app.include_router(
    clients_router,
    prefix=f"/api/{settings.API_VERSION}/clients",
    tags=["Clients"]
)

app.include_router(
    activities_router,
    prefix=f"/api/{settings.API_VERSION}/activities",
    tags=["Activities"]
)


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "version": settings.API_VERSION,
        "docs": "/docs" if settings.DEBUG else "Documentation disabled in production"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )