"""
Conexión a la base de datos.
Define el engine de SQLModel, la creación de tablas y la dependencia de sesión.
"""

from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine, text

from musica_api.config import settings

# check_same_thread solo aplica para SQLite (FastAPI usa varios hilos)
connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(settings.database_url, echo=False, connect_args=connect_args)


def create_db_and_tables() -> None:
    """Crea todas las tablas definidas en los modelos."""
    # Importar los modelos para que queden registrados en el metadata
    from musica_api import models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Dependencia de FastAPI que entrega una sesión por request."""
    with Session(engine) as session:
        yield session


def check_db_connection() -> bool:
    """Verifica que la base de datos responda."""
    try:
        with Session(engine) as session:
            session.exec(text("SELECT 1"))
        return True
    except Exception:
        return False
