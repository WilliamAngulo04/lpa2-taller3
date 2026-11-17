"""Endpoints para la gestión de favoritos."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from musica_api.database import get_session
from musica_api.logging_config import get_logger
from musica_api.models import Cancion, Favorito, FavoritoCreate, FavoritoRead, Usuario
from musica_api.paginacion import Pagina, ParametrosPaginacion, paginar

router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=Pagina[FavoritoRead])
def listar_favoritos(
    params: ParametrosPaginacion = Depends(),
    session: Session = Depends(get_session),
):
    """Lista los favoritos de forma paginada."""
    return paginar(session, select(Favorito).order_by(Favorito.id), params)


@router.post("", response_model=FavoritoRead, status_code=status.HTTP_201_CREATED)
def crear_favorito(datos: FavoritoCreate, session: Session = Depends(get_session)):
    """Marca una canción como favorita de un usuario."""
    if not session.get(Usuario, datos.id_usuario):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    if not session.get(Cancion, datos.id_cancion):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Canción no encontrada")
    favorito = Favorito.model_validate(datos)
    session.add(favorito)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, "La canción ya está en favoritos"
        ) from None
    session.refresh(favorito)
    logger.info("Favorito creado: id=%s", favorito.id)
    return favorito


@router.get("/{id_favorito}", response_model=FavoritoRead)
def obtener_favorito(id_favorito: int, session: Session = Depends(get_session)):
    """Obtiene un favorito por su ID."""
    favorito = session.get(Favorito, id_favorito)
    if not favorito:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Favorito no encontrado")
    return favorito


@router.delete("/{id_favorito}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_favorito(id_favorito: int, session: Session = Depends(get_session)):
    """Elimina un favorito."""
    favorito = session.get(Favorito, id_favorito)
    if not favorito:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Favorito no encontrado")
    session.delete(favorito)
    session.commit()
    logger.info("Favorito eliminado: id=%s", id_favorito)
