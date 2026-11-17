"""Endpoints para la gestión de usuarios y sus favoritos."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from musica_api.database import get_session
from musica_api.logging_config import get_logger
from musica_api.models import (
    Cancion,
    Favorito,
    FavoritoRead,
    Usuario,
    UsuarioCreate,
    UsuarioRead,
    UsuarioUpdate,
)
from musica_api.paginacion import Pagina, ParametrosPaginacion, paginar
from musica_api.seguridad import get_usuario_actual

router = APIRouter()
logger = get_logger(__name__)

# Los endpoints de escritura exigen un token OAuth2 válido
PROTEGIDO = [Depends(get_usuario_actual)]


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
        logger.warning("Correo duplicado: %s", correo)
        raise HTTPException(status.HTTP_409_CONFLICT, "El correo ya está registrado")


@router.get("", response_model=Pagina[UsuarioRead])
def listar_usuarios(
    params: ParametrosPaginacion = Depends(),
    session: Session = Depends(get_session),
):
    """Lista los usuarios de forma paginada."""
    return paginar(session, select(Usuario).order_by(Usuario.id), params)


@router.post(
    "",
    response_model=UsuarioRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=PROTEGIDO,
)
def crear_usuario(datos: UsuarioCreate, session: Session = Depends(get_session)):
    """Crea un usuario. El correo debe ser único."""
    verificar_correo_disponible(session, datos.correo)
    usuario = Usuario.model_validate(datos)
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    logger.info("Usuario creado: id=%s correo=%s", usuario.id, usuario.correo)
    return usuario


@router.get("/{id_usuario}", response_model=UsuarioRead)
def obtener_usuario(id_usuario: int, session: Session = Depends(get_session)):
    """Obtiene un usuario por su ID."""
    return obtener_usuario_o_404(session, id_usuario)


@router.put("/{id_usuario}", response_model=UsuarioRead, dependencies=PROTEGIDO)
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


@router.delete(
    "/{id_usuario}", status_code=status.HTTP_204_NO_CONTENT, dependencies=PROTEGIDO
)
def eliminar_usuario(id_usuario: int, session: Session = Depends(get_session)):
    """Elimina un usuario y sus favoritos."""
    usuario = obtener_usuario_o_404(session, id_usuario)
    favoritos = session.exec(select(Favorito).where(Favorito.id_usuario == id_usuario))
    for favorito in favoritos:
        session.delete(favorito)
    session.delete(usuario)
    session.commit()
    logger.info("Usuario eliminado: id=%s", id_usuario)


# -----------------------------------------------------------------------------
# Favoritos de un usuario
# -----------------------------------------------------------------------------


@router.get("/{id_usuario}/favoritos", response_model=Pagina[FavoritoRead])
def listar_favoritos_usuario(
    id_usuario: int,
    params: ParametrosPaginacion = Depends(),
    session: Session = Depends(get_session),
):
    """Lista los favoritos de un usuario de forma paginada."""
    obtener_usuario_o_404(session, id_usuario)
    consulta = (
        select(Favorito).where(Favorito.id_usuario == id_usuario).order_by(Favorito.id)
    )
    return paginar(session, consulta, params)


@router.post(
    "/{id_usuario}/favoritos/{id_cancion}",
    response_model=FavoritoRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=PROTEGIDO,
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
    logger.info("Favorito marcado: usuario=%s cancion=%s", id_usuario, id_cancion)
    return favorito


@router.delete(
    "/{id_usuario}/favoritos/{id_cancion}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=PROTEGIDO,
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
