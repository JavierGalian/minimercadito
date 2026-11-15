from fastapi.testclient import TestClient


def test_login_returns_bearer_token_and_role(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "AdminTestPass123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["rol"] == "ADMIN"
    assert body["access_token"]


def test_login_rejects_invalid_password(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "IncorrectPassword"},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_login_rejects_inactive_user(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "inactivo", "password": "InactiveTestPass123"},
    )

    assert response.status_code == 401


def test_product_creation_requires_admin(
    client: TestClient,
    cashier_headers: dict[str, str],
) -> None:
    payload = {
        "nombre": "Producto",
        "precio": "120.00",
        "stock_actual": 2,
    }

    unauthorized = client.post("/api/productos", json=payload)
    forbidden = client.post(
        "/api/productos",
        json=payload,
        headers=cashier_headers,
    )

    assert unauthorized.status_code == 401
    assert forbidden.status_code == 403


def test_invalid_bearer_token_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/productos",
        json={
            "nombre": "Producto",
            "precio": "120.00",
            "stock_actual": 2,
        },
        headers={"Authorization": "Bearer token-invalido"},
    )

    assert response.status_code == 401
