"""
Application Configuration Settings.
Reads environment variables with sensible defaults.
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Powered Image Quality & Defect Detection"
    API_V1_PREFIX: str = "/api/v1"
    
    BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    STORAGE_DIR: str = os.path.join(BASE_DIR, "backend/storage")
    UPLOADS_DIR: str = os.path.join(STORAGE_DIR, "uploads")
    HEATMAPS_DIR: str = os.path.join(STORAGE_DIR, "heatmaps")
    MODELS_DIR: str = os.path.join(BASE_DIR, "backend/models_store")
    
    DATABASE_URL: str = f"sqlite:///{os.path.join(BASE_DIR, 'backend/quality_detector.db')}"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOADS_DIR, exist_ok=True)
os.makedirs(settings.HEATMAPS_DIR, exist_ok=True)
os.makedirs(settings.MODELS_DIR, exist_ok=True)
