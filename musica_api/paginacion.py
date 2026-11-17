"""
Paginación de resultados.

Los endpoints de listado reciben los parámetros `pagina` y `tamaño` y
responden con un objeto `Pagina` que incluye el total de registros.
"""

import math
from typing import TypeVar

from fastapi import Query
from pydantic import BaseModel
from sqlmodel import Session, func, select
from sqlmodel.sql.expression import SelectOfScalar

from musica_api.config import settings

T = TypeVar("T")


class Pagina[T](BaseModel):
    """Respuesta paginada genérica."""

    total: int
    pagina: int
    tamaño: int
    paginas: int
    items: list[T]


class ParametrosPaginacion:
    """Dependencia de FastAPI con los parámetros de paginación."""

    def __init__(
        self,
        pagina: int = Query(1, ge=1, description="Número de página (desde 1)"),
        tamaño: int = Query(
            settings.page_size_default,
            ge=1,
            le=settings.page_size_max,
            description="Cantidad de elementos por página",
        ),
    ):
        self.pagina = pagina
        self.tamaño = tamaño


def paginar(
    session: Session, consulta: SelectOfScalar, params: ParametrosPaginacion
) -> dict:
    """Ejecuta la consulta aplicando OFFSET/LIMIT y cuenta el total."""
    total = session.exec(
        select(func.count()).select_from(consulta.order_by(None).subquery())
    ).one()
    items = session.exec(
        consulta.offset((params.pagina - 1) * params.tamaño).limit(params.tamaño)
    ).all()
    return {
        "total": total,
        "pagina": params.pagina,
        "tamaño": params.tamaño,
        "paginas": math.ceil(total / params.tamaño),
        "items": items,
    }
