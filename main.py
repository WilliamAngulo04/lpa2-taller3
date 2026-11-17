import logging
import platform
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from musica_api.config import settings
from musica_api.database import check_db_connection, create_db_and_tables
from musica_api.logging_config import get_logger, setup_logging
from musica_api.routers import auth, canciones, favoritos, usuarios

INICIO = time.time()

setup_logging(settings)
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestor de ciclo de vida de la aplicación.
    Se ejecuta al iniciar y al cerrar la aplicación.
    """
    # Startup: Crear tablas en la base de datos
    logger.info(
        "Iniciando %s v%s (entorno: %s)",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )
    create_db_and_tables()
    logger.info("Base de datos lista: %s", settings.database_url)
    yield

    # Shutdown: Limpiar recursos si es necesario
    logger.info("Cerrando aplicación...")


# Crear la instancia de FastAPI con metadatos apropiados
# Incluir: title, description, version, contact, license_info
app = FastAPI(
    title=settings.app_name,
    description="API RESTful para gestionar usuarios, canciones y favoritos",
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
    contact={
        "name": "Equipo API de Música",
        "url": "https://github.com/UR-CC/lpa2-taller3",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)


# Configurar CORS para permitir solicitudes desde diferentes orígenes
# Esto es importante para desarrollo con frontend separado
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # En producción, orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Incluir los routers de usuarios, canciones y favoritos
app.include_router(auth.router, prefix="/api/auth", tags=["Autenticación"])
app.include_router(usuarios.router, prefix="/api/usuarios", tags=["Usuarios"])
app.include_router(canciones.router, prefix="/api/canciones", tags=["Canciones"])
app.include_router(favoritos.router, prefix="/api/favoritos", tags=["Favoritos"])


# Crear un endpoint raíz que retorne información básica de la API
@app.get("/", tags=["Root"])
async def root():
    """
    Endpoint raíz de la API.
    Retorna información básica y enlaces a la documentación.
    """
    return {
        "nombre": settings.app_name,
        "version": settings.app_version,
        "entorno": settings.environment,
        "documentacion": {"swagger": "/docs", "redoc": "/redoc"},
        "endpoints": {
            "usuarios": "/api/usuarios",
            "canciones": "/api/canciones",
            "favoritos": "/api/favoritos",
        },
    }


# Crear un endpoint de health check para monitoreo
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint para verificar el estado de la API.
    Útil para sistemas de monitoreo y orquestación.
    """
    db_ok = check_db_connection()
    return {
        "status": "healthy" if db_ok else "unhealthy",
        "database": "conectada" if db_ok else "sin conexión",
        "uptime_segundos": round(time.time() - INICIO, 2),
        "version": settings.app_version,
        "python": platform.python_version(),
        "sistema": platform.system(),
    }


# Middleware para logging de requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Registra método, ruta, código de estado y tiempo de cada request."""
    inicio = time.perf_counter()
    response = await call_next(request)
    duracion_ms = (time.perf_counter() - inicio) * 1000
    cliente = request.client.host if request.client else "-"
    nivel = (
        logging.ERROR
        if response.status_code >= 500
        else logging.WARNING
        if response.status_code >= 400
        else logging.INFO
    )
    logger.log(
        nivel,
        "%s %s -> %d (%.1f ms) [%s]",
        request.method,
        request.url.path,
        response.status_code,
        duracion_ms,
        cliente,
    )
    response.headers["X-Process-Time-Ms"] = f"{duracion_ms:.1f}"
    return response


# Manejadores de errores personalizados
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.exception("Error de base de datos en %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno de base de datos"},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Error no controlado en %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
