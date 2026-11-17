"""
Modelos de datos de la API de Música.

Cada entidad tiene:
- un modelo base con los campos y sus validaciones (Pydantic),
- un modelo de tabla (SQLModel, table=True),
- modelos para crear, actualizar y leer (esquemas de entrada/salida).
"""

from datetime import UTC, datetime

from pydantic import field_validator
from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

from utils import obtener_año_actual, validar_año, validar_correo


def ahora() -> datetime:
    """Fecha y hora actual en UTC (SQLModel exige fechas con zona horaria)."""
    return datetime.now(UTC)


# =============================================================================
# USUARIO
# =============================================================================


class UsuarioBase(SQLModel):
    nombre: str = Field(min_length=2, max_length=100)
    correo: str = Field(max_length=150, index=True, unique=True)

    @field_validator("nombre")
    @classmethod
    def nombre_no_vacio(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El nombre no puede estar vacío")
        return v

    @field_validator("correo")
    @classmethod
    def correo_valido(cls, v: str) -> str:
        v = v.strip().lower()
        if not validar_correo(v):
            raise ValueError("Correo electrónico inválido")
        return v


class Usuario(UsuarioBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    fecha_registro: datetime = Field(default_factory=ahora)
    # Hash bcrypt; None para usuarios creados sin contraseña (no pueden iniciar sesión)
    password_hash: str | None = Field(default=None, max_length=100)


class UsuarioCreate(UsuarioBase):
    pass


class UsuarioRegistro(UsuarioBase):
    # bcrypt solo usa los primeros 72 bytes
    password: str = Field(min_length=8, max_length=72)


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class UsuarioUpdate(SQLModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=100)
    correo: str | None = Field(default=None, max_length=150)

    @field_validator("correo")
    @classmethod
    def correo_valido(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip().lower()
        if not validar_correo(v):
            raise ValueError("Correo electrónico inválido")
        return v


class UsuarioRead(UsuarioBase):
    id: int
    fecha_registro: datetime


# =============================================================================
# CANCIÓN
# =============================================================================


def _validar_año_cancion(v: int | None) -> int | None:
    if v is not None and not validar_año(v):
        raise ValueError(f"El año debe estar entre 1900 y {obtener_año_actual()}")
    return v


class CancionBase(SQLModel):
    titulo: str = Field(min_length=1, max_length=200, index=True)
    artista: str = Field(min_length=1, max_length=150, index=True)
    album: str | None = Field(default=None, max_length=200)
    duracion: int = Field(gt=0, description="Duración en segundos")
    año: int = Field(description="Año de lanzamiento")
    genero: str = Field(min_length=1, max_length=50, index=True)

    @field_validator("año")
    @classmethod
    def año_valido(cls, v: int) -> int:
        return _validar_año_cancion(v)


class Cancion(CancionBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    fecha_creacion: datetime = Field(default_factory=ahora)


class CancionCreate(CancionBase):
    pass


class CancionUpdate(SQLModel):
    titulo: str | None = Field(default=None, min_length=1, max_length=200)
    artista: str | None = Field(default=None, min_length=1, max_length=150)
    album: str | None = Field(default=None, max_length=200)
    duracion: int | None = Field(default=None, gt=0)
    año: int | None = None
    genero: str | None = Field(default=None, min_length=1, max_length=50)

    @field_validator("año")
    @classmethod
    def año_valido(cls, v: int | None) -> int | None:
        return _validar_año_cancion(v)


class CancionRead(CancionBase):
    id: int
    fecha_creacion: datetime


# =============================================================================
# FAVORITO
# =============================================================================


class FavoritoBase(SQLModel):
    id_usuario: int = Field(foreign_key="usuario.id", index=True)
    id_cancion: int = Field(foreign_key="cancion.id", index=True)


class Favorito(FavoritoBase, table=True):
    __table_args__ = (
        UniqueConstraint("id_usuario", "id_cancion", name="uq_usuario_cancion"),
    )

    id: int | None = Field(default=None, primary_key=True)
    fecha_marcado: datetime = Field(default_factory=ahora)


class FavoritoCreate(FavoritoBase):
    pass


class FavoritoRead(FavoritoBase):
    id: int
    fecha_marcado: datetime
