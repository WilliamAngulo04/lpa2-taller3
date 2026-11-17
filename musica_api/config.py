"""
Configuración de la aplicación.
Maneja diferentes entornos: desarrollo, pruebas y producción.
"""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración de la aplicación usando Pydantic Settings.
    Lee las variables de entorno desde el archivo .env
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Configuración básica de la aplicación
    app_name: str = "API de Música"
    app_version: str = "1.0.0"

    # Configuración del entorno
    environment: Literal["development", "testing", "production"] = "development"

    # Configuración de la base de datos
    # Para SQLite: sqlite:///./musica.db
    # Para PostgreSQL: postgresql://user:password@localhost/dbname
    database_url: str = "sqlite:///./musica.db"

    # Configuración del servidor
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # Configuración de CORS
    # En desarrollo puedes usar ["*"], en producción especifica los orígenes permitidos
    cors_origins: list[str] = ["*"]

    # Configuración de seguridad (para futuras mejoras)
    secret_key: str = "cambiar-esta-clave-en-produccion"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Configuración de logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_file: str | None = "musica_api.log"

    @field_validator("environment", mode="before")
    @classmethod
    def normalizar_environment(cls, v: str) -> str:
        return v.lower() if isinstance(v, str) else v

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v:
            raise ValueError("DATABASE_URL no puede estar vacío")
        return v

    @field_validator("log_level", mode="before")
    @classmethod
    def normalizar_log_level(cls, v: str) -> str:
        return v.upper() if isinstance(v, str) else v


# Crear diferentes configuraciones para cada entorno
class DevelopmentSettings(Settings):
    """Configuración para el entorno de desarrollo."""

    debug: bool = True
    log_level: str = "DEBUG"


class TestingSettings(Settings):
    """Configuración para el entorno de pruebas."""

    # Usar una base de datos diferente para pruebas
    database_url: str = "sqlite:///./test_musica.db"
    debug: bool = False
    log_level: str = "WARNING"
    log_file: str | None = None


class ProductionSettings(Settings):
    """Configuración para el entorno de producción."""

    debug: bool = False
    log_level: str = "INFO"
    # En producción se recomienda una base de datos más robusta (PostgreSQL, MySQL),
    # definida por la variable de entorno DATABASE_URL, p. ej.:
    # DATABASE_URL=postgresql://user:password@localhost/musica_prod


def validate_settings(config: Settings) -> None:
    """Valida que todas las configuraciones necesarias estén presentes."""
    required_settings = ["database_url", "app_name"]
    for setting in required_settings:
        if not getattr(config, setting, None):
            raise ValueError(f"Configuración requerida no encontrada: {setting}")
    if config.environment == "production" and config.secret_key.startswith("cambiar"):
        raise ValueError("Debe definir SECRET_KEY en producción")


# Función para obtener la configuración según el entorno
@lru_cache
def get_settings() -> Settings:
    """
    Retorna la configuración apropiada según el entorno.
    """
    env = Settings().environment

    if env == "testing":
        config = TestingSettings()
    elif env == "production":
        config = ProductionSettings()
    else:
        config = DevelopmentSettings()

    validate_settings(config)
    return config


# Instancia global de configuración
settings = get_settings()
