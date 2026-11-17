"""
Sistema de registro (logging) de la aplicación.

- Escribe en consola y, si LOG_FILE está definido, en un archivo con rotación.
- El nivel se controla con la variable de entorno LOG_LEVEL.
- Cada módulo obtiene su logger con `get_logger(__name__)`.
"""

import logging
from logging.handlers import RotatingFileHandler

from musica_api.config import Settings

FORMATO = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOGGER_RAIZ = "musica_api"


def setup_logging(config: Settings) -> logging.Logger:
    """Configura los handlers del logger principal de la aplicación."""
    logger = logging.getLogger(LOGGER_RAIZ)
    logger.setLevel(config.log_level)
    logger.propagate = False

    # Evitar handlers duplicados si se llama más de una vez (p. ej. con --reload)
    if logger.handlers:
        return logger

    formatter = logging.Formatter(FORMATO, datefmt="%Y-%m-%d %H:%M:%S")

    consola = logging.StreamHandler()
    consola.setFormatter(formatter)
    logger.addHandler(consola)

    if config.log_file:
        archivo = RotatingFileHandler(
            config.log_file, maxBytes=1_000_000, backupCount=5, encoding="utf-8"
        )
        archivo.setFormatter(formatter)
        logger.addHandler(archivo)

    return logger


def get_logger(nombre: str) -> logging.Logger:
    """Retorna un logger hijo del logger principal."""
    if not nombre.startswith(LOGGER_RAIZ):
        nombre = f"{LOGGER_RAIZ}.{nombre}"
    return logging.getLogger(nombre)
