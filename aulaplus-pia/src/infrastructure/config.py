"""Configuración 12-factor: todo viene de variables de entorno (ver .env.example)."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    app_env: str = "development"
    api_title: str = "AulaPlus API"

    @staticmethod
    def from_env() -> "Settings":
        url = os.getenv("DATABASE_URL", "sqlite:///./aulaplus.db")
        if url.startswith("postgres://"):  # Render/Heroku usan este esquema; SQLAlchemy espera postgresql://
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return Settings(
            database_url=url,
            app_env=os.getenv("APP_ENV", "development"),
        )
