from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..api.deps import require_role
from ..core.database import get_db
from ..core.exceptions import ConflictError, NotFoundError
from ..core.security import hash_password
from ..models.models import UserModel
from ..schemas.schemas import UserCreate, UserResponse

router = APIRouter()


@router.get("", response_model=list[UserResponse])
def listar_usuarios(
    db: Session = Depends(get_db),
    _: UserModel = Depends(require_role(["ADMIN"])),
) -> list[UserModel]:
    return list(db.scalars(select(UserModel).order_by(UserModel.id)).all())


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_usuario(
    datos: UserCreate,
    db: Session = Depends(get_db),
    _: UserModel = Depends(require_role(["ADMIN"])),
) -> UserModel:
    existing_user = db.scalar(
        select(UserModel.id).where(UserModel.username == datos.username),
    )
    if existing_user is not None:
        raise ConflictError("Ya existe un usuario con ese nombre.")

    user = UserModel(
        username=datos.username,
        hashed_password=hash_password(datos.password),
        rol=datos.rol,
        activo=True,
    )
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "No se pudo crear el usuario por un conflicto de datos."
        ) from exc
    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def desactivar_usuario(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role(["ADMIN"])),
) -> Response:
    if user_id == current_user.id:
        raise ConflictError("No podés desactivar tu propio usuario.")

    user = db.get(UserModel, user_id)
    if user is None:
        raise NotFoundError("No se encontró el usuario solicitado.")

    user.activo = False
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
