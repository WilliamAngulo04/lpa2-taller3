"""
Autenticación con OAuth2 (flujo de contraseña) y tokens JWT.

- Las contraseñas se guardan cifradas con bcrypt.
- `POST /api/auth/token` entrega un JWT firmado con `SECRET_KEY`.
- La dependencia `get_usuario_actual` protege los endpoints de escritura.
"""

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from musica_api.config import settings
from musica_api.database import get_session
from musica_api.models import Usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def cifrar_password(password: str) -> str:
    """Cifra una contraseña con bcrypt (sal aleatoria incluida)."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_password(password: str, password_hash: str | None) -> bool:
    """Compara una contraseña con su hash; False si el usuario no tiene contraseña."""
    if not password_hash:
        return False
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def crear_token(id_usuario: int) -> str:
    """Crea un JWT con el ID del usuario (`sub`) y su fecha de expiración."""
    expira = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(id_usuario), "exp": expira}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def get_usuario_actual(
    token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)
) -> Usuario:
    """Dependencia que valida el token Bearer y retorna el usuario autenticado."""
    credenciales_invalidas = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        id_usuario = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise credenciales_invalidas from None
    usuario = session.get(Usuario, id_usuario)
    if not usuario:
        raise credenciales_invalidas
    return usuario
