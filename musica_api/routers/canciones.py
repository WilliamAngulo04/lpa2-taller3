"""Endpoints para la gestión de canciones."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, col, select

from musica_api.database import get_session
from musica_api.models import (
    Cancion,
    CancionCreate,
    CancionRead,
    CancionUpdate,
    Favorito,
)

router = APIRouter()


def obtener_cancion_o_404(session: Session, id_cancion: int) -> Cancion:
    cancion = session.get(Cancion, id_cancion)
    if not cancion:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Canción no encontrada")
    return cancion


@router.get("", response_model=list[CancionRead])
def listar_canciones(session: Session = Depends(get_session)):
    """Lista todas las canciones."""
    return session.exec(select(Cancion)).all()


# Debe declararse antes de /{id_cancion} para que "buscar" no se tome como ID
@router.get("/buscar", response_model=list[CancionRead])
def buscar_canciones(
    titulo: str | None = None,
    artista: str | None = None,
    genero: str | None = None,
    session: Session = Depends(get_session),
):
    """Busca canciones por título, artista y/o género (coincidencia parcial)."""
    consulta = select(Cancion)
    if titulo:
        consulta = consulta.where(col(Cancion.titulo).ilike(f"%{titulo}%"))
    if artista:
        consulta = consulta.where(col(Cancion.artista).ilike(f"%{artista}%"))
    if genero:
        consulta = consulta.where(col(Cancion.genero).ilike(f"%{genero}%"))
    return session.exec(consulta).all()


@router.post("", response_model=CancionRead, status_code=status.HTTP_201_CREATED)
def crear_cancion(datos: CancionCreate, session: Session = Depends(get_session)):
    """Crea una canción."""
    cancion = Cancion.model_validate(datos)
    session.add(cancion)
    session.commit()
    session.refresh(cancion)
    return cancion


@router.get("/{id_cancion}", response_model=CancionRead)
def obtener_cancion(id_cancion: int, session: Session = Depends(get_session)):
    """Obtiene una canción por su ID."""
    return obtener_cancion_o_404(session, id_cancion)


@router.put("/{id_cancion}", response_model=CancionRead)
def actualizar_cancion(
    id_cancion: int, datos: CancionUpdate, session: Session = Depends(get_session)
):
    """Actualiza los campos enviados de una canción."""
    cancion = obtener_cancion_o_404(session, id_cancion)
    cancion.sqlmodel_update(datos.model_dump(exclude_unset=True))
    session.add(cancion)
    session.commit()
    session.refresh(cancion)
    return cancion


@router.delete("/{id_cancion}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_cancion(id_cancion: int, session: Session = Depends(get_session)):
    """Elimina una canción y los favoritos que la referencian."""
    cancion = obtener_cancion_o_404(session, id_cancion)
    favoritos = session.exec(select(Favorito).where(Favorito.id_cancion == id_cancion))
    for favorito in favoritos:
        session.delete(favorito)
    session.delete(cancion)
    session.commit()
