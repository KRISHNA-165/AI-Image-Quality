"""
Main FastAPI Application Entrypoint.
"""

import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.config import settings
from backend.app.database import engine, Base
from backend.app.api.routes import router as api_router
from backend.app.middleware import RequestLoggingMiddleware

# Configure root logger for clean output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Create SQLite database tables if they do not exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Full-stack AI-powered image quality and visual defect detection system.",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 1. Add Request Logging & Latency Telemetry Middleware
app.add_middleware(RequestLoggingMiddleware)

# 2. Enable CORS for local development and containerized frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Mount static file directory for serving uploaded images and generated heatmaps
app.mount("/storage", StaticFiles(directory=settings.STORAGE_DIR), name="storage")

# 4. Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
def root():
    return {
        "message": "AI-Powered Image Quality & Defect Detection API is running.",
        "version": "1.1.0",
        "docs": "/docs",
        "health": "/health",
        "metrics": f"{settings.API_V1_PREFIX}/metrics",
    }

@app.get("/health")
def root_health():
    from backend.app.api.routes import evaluator
    return {
        "status": "ok",
        "model_loaded": evaluator.is_loaded,
        "cnn_model_loaded": evaluator.cnn.is_loaded,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
