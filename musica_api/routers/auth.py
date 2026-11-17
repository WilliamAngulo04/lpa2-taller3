"""Endpoints de autenticación: registro, inicio de sesión (OAuth2) y perfil."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from musica_api.database import get_session
from musica_api.logging_config import get_logger
from musica_api.models import Token, Usuario, UsuarioRead, UsuarioRegistro
from musica_api.seguridad import (
    cifrar_password,
    crear_token,
    get_usuario_actual,
    verificar_password,
)

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/registro", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED
)
def registrar(datos: UsuarioRegistro, session: Session = Depends(get_session)):
    """Crea una cuenta con nombre, correo y contraseña."""
    if session.exec(select(Usuario).where(Usuario.correo == datos.correo)).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "El correo ya está registrado")
    usuario = Usuario(
        nombre=datos.nombre,
        correo=datos.correo,
        password_hash=cifrar_password(datos.password),
    )
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    logger.info("Usuario registrado: id=%s correo=%s", usuario.id, usuario.correo)
    return usuario


@router.post("/token", response_model=Token)
def iniciar_sesion(
    form: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    """
    Inicio de sesión con el flujo de contraseña de OAuth2.
    `username` es el correo del usuario.
    """
    correo = form.username.strip().lower()
    usuario = session.exec(select(Usuario).where(Usuario.correo == correo)).first()
    if not usuario or not verificar_password(form.password, usuario.password_hash):
        logger.warning("Inicio de sesión fallido: %s", correo)
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    logger.info("Inicio de sesión: id=%s", usuario.id)
    return Token(access_token=crear_token(usuario.id))


@router.get("/me", response_model=UsuarioRead)
def perfil(usuario: Usuario = Depends(get_usuario_actual)):
    """Retorna el usuario autenticado."""
    return usuario
