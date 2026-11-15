from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.security import create_access_token, verify_password
from ..models.models import UserModel
from ..schemas.schemas import Token, UserLogin

router = APIRouter()


@router.post("/login", response_model=Token)
def login(
    credentials: UserLogin,
    db: Annotated[Session, Depends(get_db)],
) -> Token:
    user = db.scalar(
        select(UserModel).where(UserModel.username == credentials.username),
    )
    if (
        user is None
        or not user.activo
        or not verify_password(credentials.password, user.hashed_password)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return Token(
        access_token=create_access_token(user.username, user.rol),
        rol=user.rol,
    )
