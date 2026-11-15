from fastapi.testclient import TestClient


def test_create_product(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/productos",
        json={
            "nombre": "Yerba mate",
            "codigo_barras": "7791234567890",
            "precio": "2450.50",
            "stock_actual": 12,
        },
        headers=admin_headers,
    )

    assert response.status_code == 201
    product = response.json()
    assert product["nombre"] == "Yerba mate"
    assert product["codigo_barras"] == "7791234567890"
    assert product["precio"] == "2450.50"
    assert product["stock_actual"] == 12


def test_duplicate_barcode_returns_structured_conflict(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    payload = {
        "nombre": "Producto",
        "codigo_barras": "7791234567890",
        "precio": "120.00",
        "stock_actual": 2,
    }
    assert client.post(
        "/api/productos",
        json=payload,
        headers=admin_headers,
    ).status_code == 201

    response = client.post(
        "/api/productos",
        json={**payload, "nombre": "Producto duplicado"},
        headers=admin_headers,
    )

    assert response.status_code == 409
    assert response.json() == {
        "code": "conflict",
        "detail": "Ya existe un producto con ese código de barras.",
    }


def test_missing_barcode_returns_structured_not_found(
    client: TestClient,
) -> None:
    response = client.get("/api/productos/codigo-barras/no-existe")

    assert response.status_code == 404
    assert response.json() == {
        "code": "not_found",
        "detail": "No se encontró el producto.",
    }
