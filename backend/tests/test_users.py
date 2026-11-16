from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.models import UserModel


def test_admin_can_create_and_list_users(
    client: TestClient,
    admin_headers: dict[str, str],
    engine: Engine,
) -> None:
    response = client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "username": "nuevo-cajero",
            "password": "StrongPassword123!",
            "rol": "CAJERO",
        },
    )

    assert response.status_code == 201
    created_user = response.json()
    assert created_user["username"] == "nuevo-cajero"
    assert created_user["rol"] == "CAJERO"
    assert created_user["activo"] is True
    assert "hashed_password" not in created_user

    with Session(engine) as db:
        user = db.scalar(
            select(UserModel).where(UserModel.username == "nuevo-cajero"),
        )
        assert user is not None
        assert user.hashed_password != "StrongPassword123!"
        assert verify_password("StrongPassword123!", user.hashed_password)

    listing = client.get("/api/users", headers=admin_headers)
    assert listing.status_code == 200
    assert any(item["username"] == "nuevo-cajero" for item in listing.json())


def test_admin_can_create_repositor_user(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "username": "nuevo-repositor",
            "password": "StrongPassword123!",
            "rol": "REPOSITOR",
        },
    )

    assert response.status_code == 201
    assert response.json()["rol"] == "REPOSITOR"


def test_admin_cannot_create_duplicate_username(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "username": "admin",
            "password": "StrongPassword123!",
            "rol": "ADMIN",
        },
    )

    assert response.status_code == 409
    assert response.json()["code"] == "conflict"


def test_cashier_cannot_manage_users(
    client: TestClient,
    cashier_headers: dict[str, str],
) -> None:
    payload = {
        "username": "otro-cajero",
        "password": "StrongPassword123!",
        "rol": "CAJERO",
    }

    assert client.get("/api/users", headers=cashier_headers).status_code == 403
    assert (
        client.post("/api/users", headers=cashier_headers, json=payload).status_code
        == 403
    )
    assert (
        client.delete("/api/users/1", headers=cashier_headers).status_code == 403
    )
    assert (
        client.patch(
            "/api/users/1",
            headers=cashier_headers,
            json={"rol": "ADMIN"},
        ).status_code
        == 403
    )


def test_admin_can_deactivate_other_users_but_not_self(
    client: TestClient,
    admin_headers: dict[str, str],
    engine: Engine,
) -> None:
    with Session(engine) as db:
        cashier_id = db.scalar(
            select(UserModel.id).where(UserModel.username == "cajero"),
        )
        admin_id = db.scalar(
            select(UserModel.id).where(UserModel.username == "admin"),
        )
    assert cashier_id is not None
    assert admin_id is not None

    deactivated = client.delete(
        f"/api/users/{cashier_id}",
        headers=admin_headers,
    )
    assert deactivated.status_code == 204

    login = client.post(
        "/api/auth/login",
        json={"username": "cajero", "password": "CajeroTestPass123"},
    )
    assert login.status_code == 401

    self_deactivation = client.delete(
        f"/api/users/{admin_id}",
        headers=admin_headers,
    )
    assert self_deactivation.status_code == 409


def test_admin_can_update_user_and_password_is_hashed(
    client: TestClient,
    admin_headers: dict[str, str],
    engine: Engine,
) -> None:
    with Session(engine) as db:
        cashier_id = db.scalar(
            select(UserModel.id).where(UserModel.username == "cajero"),
        )
    assert cashier_id is not None

    response = client.patch(
        f"/api/users/{cashier_id}",
        headers=admin_headers,
        json={
            "username": "cajero-nuevo",
            "password": "NewStrongPassword123!",
            "rol": "REPOSITOR",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": cashier_id,
        "username": "cajero-nuevo",
        "rol": "REPOSITOR",
        "activo": True,
    }
    with Session(engine) as db:
        updated_user = db.get(UserModel, cashier_id)
        assert updated_user is not None
        assert verify_password(
            "NewStrongPassword123!",
            updated_user.hashed_password,
        )
        assert updated_user.hashed_password != "NewStrongPassword123!"

    assert client.post(
        "/api/auth/login",
        json={"username": "cajero-nuevo", "password": "CajeroTestPass123"},
    ).status_code == 401
    assert client.post(
        "/api/auth/login",
        json={"username": "cajero-nuevo", "password": "NewStrongPassword123!"},
    ).status_code == 200


def test_admin_user_update_validates_not_found_duplicate_and_self_downgrade(
    client: TestClient,
    admin_headers: dict[str, str],
    engine: Engine,
) -> None:
    with Session(engine) as db:
        admin_id = db.scalar(
            select(UserModel.id).where(UserModel.username == "admin"),
        )
        cashier_id = db.scalar(
            select(UserModel.id).where(UserModel.username == "cajero"),
        )
    assert admin_id is not None
    assert cashier_id is not None

    not_found = client.patch(
        "/api/users/9999",
        headers=admin_headers,
        json={"rol": "CAJERO"},
    )
    duplicate = client.patch(
        f"/api/users/{cashier_id}",
        headers=admin_headers,
        json={"username": "admin"},
    )
    self_downgrade = client.patch(
        f"/api/users/{admin_id}",
        headers=admin_headers,
        json={"rol": "CAJERO"},
    )
    empty_update = client.patch(
        f"/api/users/{cashier_id}",
        headers=admin_headers,
        json={},
    )

    assert not_found.status_code == 404
    assert duplicate.status_code == 409
    assert self_downgrade.status_code == 409
    assert empty_update.status_code == 422
