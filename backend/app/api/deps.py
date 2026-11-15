from collections.abc import Callable, Sequence
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.security import decode_access_token
from ..models.models import UserModel

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    db: Annotated[Session, Depends(get_db)],
) -> UserModel:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales de autenticación inválidas o vencidas.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise unauthorized

    user = db.scalar(
        select(UserModel).where(UserModel.username == payload["sub"]),
    )
    if user is None or not user.activo:
        raise unauthorized
    return user


def require_role(
    roles: Sequence[str],
) -> Callable[[Annotated[UserModel, Depends(get_current_user)]], UserModel]:
    allowed_roles = frozenset(roles)
    if not allowed_roles:
        raise ValueError("Se debe indicar al menos un rol permitido.")

    def role_dependency(
        current_user: Annotated[UserModel, Depends(get_current_user)],
    ) -> UserModel:
        if current_user.rol not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tenés permisos para realizar esta operación.",
            )
        return current_user

    return role_dependency


require_inventory_manager = require_role(["ADMIN", "REPOSITOR"])
