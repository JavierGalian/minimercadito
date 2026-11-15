import argparse
from getpass import getpass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .core.database import get_session_factory
from .core.security import hash_password
from .models.models import UserModel
from .schemas.schemas import UserCreate


def create_user(username: str, rol: str) -> None:
    password = getpass("Contraseña (mínimo 12 caracteres): ")
    confirmation = getpass("Confirmá la contraseña: ")
    if password != confirmation:
        raise ValueError("Las contraseñas no coinciden.")

    user_data = UserCreate(username=username, password=password, rol=rol)
    session = get_session_factory()()
    try:
        existing_user = session.scalar(
            select(UserModel.id).where(UserModel.username == user_data.username),
        )
        if existing_user is not None:
            raise ValueError("Ya existe un usuario con ese nombre.")

        session.add(
            UserModel(
                username=user_data.username,
                hashed_password=hash_password(user_data.password),
                rol=user_data.rol,
                activo=True,
            )
        )
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ValueError("No se pudo crear el usuario por un conflicto de datos.") from exc
    finally:
        session.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Administración de usuarios.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    create_parser = subparsers.add_parser(
        "create-user",
        help="Crear un usuario sin exponer su contraseña en argumentos.",
    )
    create_parser.add_argument("--username", required=True)
    create_parser.add_argument("--role", choices=["ADMIN", "CAJERO"], required=True)
    args = parser.parse_args()

    try:
        if args.command == "create-user":
            create_user(args.username, args.role)
            print(f"Usuario '{args.username}' creado con rol {args.role}.")
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
