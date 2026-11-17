"""Endpoints para la gestión de usuarios y sus favoritos."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from musica_api.database import get_session
from musica_api.models import (
    Cancion,
    Favorito,
    FavoritoRead,
    Usuario,
    UsuarioCreate,
    UsuarioRead,
    UsuarioUpdate,
)

router = APIRouter()


def obtener_usuario_o_404(session: Session, id_usuario: int) -> Usuario:
    usuario = session.get(Usuario, id_usuario)
    if not usuario:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    return usuario


def verificar_correo_disponible(
    session: Session, correo: str, excluir_id: int | None = None
) -> None:
    existente = session.exec(select(Usuario).where(Usuario.correo == correo)).first()
    if existente and existente.id != excluir_id:
        raise HTTPException(status.HTTP_409_CONFLICT, "El correo ya está registrado")


@router.get("", response_model=list[UsuarioRead])
def listar_usuarios(session: Session = Depends(get_session)):
    """Lista todos los usuarios."""
    return session.exec(select(Usuario)).all()


@router.post("", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
def crear_usuario(datos: UsuarioCreate, session: Session = Depends(get_session)):
    """Crea un usuario. El correo debe ser único."""
    verificar_correo_disponible(session, datos.correo)
    usuario = Usuario.model_validate(datos)
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


@router.get("/{id_usuario}", response_model=UsuarioRead)
def obtener_usuario(id_usuario: int, session: Session = Depends(get_session)):
    """Obtiene un usuario por su ID."""
    return obtener_usuario_o_404(session, id_usuario)


@router.put("/{id_usuario}", response_model=UsuarioRead)
def actualizar_usuario(
    id_usuario: int, datos: UsuarioUpdate, session: Session = Depends(get_session)
):
    """Actualiza los campos enviados de un usuario."""
    usuario = obtener_usuario_o_404(session, id_usuario)
    cambios = datos.model_dump(exclude_unset=True)
    if "correo" in cambios:
        verificar_correo_disponible(session, cambios["correo"], excluir_id=id_usuario)
    usuario.sqlmodel_update(cambios)
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


@router.delete("/{id_usuario}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_usuario(id_usuario: int, session: Session = Depends(get_session)):
    """Elimina un usuario y sus favoritos."""
    usuario = obtener_usuario_o_404(session, id_usuario)
    favoritos = session.exec(select(Favorito).where(Favorito.id_usuario == id_usuario))
    for favorito in favoritos:
        session.delete(favorito)
    session.delete(usuario)
    session.commit()


# -----------------------------------------------------------------------------
# Favoritos de un usuario
# -----------------------------------------------------------------------------


@router.get("/{id_usuario}/favoritos", response_model=list[FavoritoRead])
def listar_favoritos_usuario(id_usuario: int, session: Session = Depends(get_session)):
    """Lista los favoritos de un usuario."""
    obtener_usuario_o_404(session, id_usuario)
    return session.exec(select(Favorito).where(Favorito.id_usuario == id_usuario)).all()


@router.post(
    "/{id_usuario}/favoritos/{id_cancion}",
    response_model=FavoritoRead,
    status_code=status.HTTP_201_CREATED,
)
def marcar_favorito_usuario(
    id_usuario: int, id_cancion: int, session: Session = Depends(get_session)
):
    """Marca una canción como favorita para un usuario."""
    obtener_usuario_o_404(session, id_usuario)
    if not session.get(Cancion, id_cancion):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Canción no encontrada")
    favorito = Favorito(id_usuario=id_usuario, id_cancion=id_cancion)
    session.add(favorito)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, "La canción ya está en favoritos"
        ) from None
    session.refresh(favorito)
    return favorito


@router.delete(
    "/{id_usuario}/favoritos/{id_cancion}", status_code=status.HTTP_204_NO_CONTENT
)
def eliminar_favorito_usuario(
    id_usuario: int, id_cancion: int, session: Session = Depends(get_session)
):
    """Quita una canción de los favoritos de un usuario."""
    favorito = session.exec(
        select(Favorito).where(
            Favorito.id_usuario == id_usuario, Favorito.id_cancion == id_cancion
        )
    ).first()
    if not favorito:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Favorito no encontrado")
    session.delete(favorito)
    session.commit()
