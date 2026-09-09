"""Application Configuration."""
import os
from typing import List
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "AI Railway Traffic Optimization System")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "railway-ai-super-secret-production-key-change-in-prod-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'railway_ai.db'}")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Simulation
    DEFAULT_SIMULATION_TICK_RATE: float = float(os.getenv("DEFAULT_SIMULATION_TICK_RATE", "1.0"))
    MAX_ACCELERATION_FACTOR: float = float(os.getenv("MAX_ACCELERATION_FACTOR", "60.0"))
    DEFAULT_HEADWAY_SECONDS: int = int(os.getenv("DEFAULT_HEADWAY_SECONDS", "180"))
    
    # AI & Modeling
    MODEL_REGISTRY_PATH: str = str(BASE_DIR / "ai" / "registry" / "models")
    RANDOM_SEED: int = int(os.getenv("RANDOM_SEED", "42"))
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # Metrics
    ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "True").lower() in ("true", "1", "yes")

settings = Settings()
