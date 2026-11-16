from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from ..api.deps import require_role
from ..core.database import get_db
from ..core.exceptions import ConflictError, NotFoundError
from ..core.security import hash_password
from ..models.models import UserModel
from ..schemas.schemas import UserCreate, UserResponse, UserUpdate

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


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
)
def actualizar_usuario(
    user_id: int,
    datos: UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role(["ADMIN"])),
) -> UserModel:
    user = db.get(UserModel, user_id)
    if user is None:
        raise NotFoundError("No se encontró el usuario solicitado.")

    cambios = datos.model_dump(exclude_unset=True)
    if user.id == current_user.id and cambios.get("rol", user.rol) != "ADMIN":
        raise ConflictError("No podés quitarte el rol de administrador.")

    username = cambios.get("username")
    if username is not None:
        duplicate = db.scalar(
            select(UserModel.id).where(
                UserModel.username == username,
                UserModel.id != user_id,
            ),
        )
        if duplicate is not None:
            raise ConflictError("Ya existe un usuario con ese nombre.")

    password = cambios.pop("password", None)
    if password is not None:
        cambios["hashed_password"] = hash_password(password)

    try:
        for field, value in cambios.items():
            setattr(user, field, value)
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "No se pudo actualizar el usuario por un conflicto de datos."
        ) from exc
    except SQLAlchemyError:
        db.rollback()
        raise
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
    active_admins = db.scalars(
        select(UserModel)
        .where(
            UserModel.rol == "ADMIN",
            UserModel.activo.is_(True),
        )
        .order_by(UserModel.id)
        .with_for_update(),
    ).all()
    user = db.get(UserModel, user_id)
    if user is None:
        raise NotFoundError("No se encontró el usuario solicitado.")
    if not user.activo:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    if user_id == current_user.id:
        raise ConflictError("No podés desactivar tu propio usuario.")
    if user.rol == "ADMIN" and len(active_admins) <= 1:
        raise ConflictError("No se puede desactivar al último administrador activo.")

    user.activo = False
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return Response(status_code=status.HTTP_204_NO_CONTENT)
