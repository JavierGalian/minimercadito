from datetime import datetime, timezone
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.models.models import InventoryMovementModel, Producto, Venta


def create_product(
    client: TestClient,
    headers: dict[str, str],
    *,
    name: str,
    barcode: str,
    price: str,
    stock: int,
) -> dict[str, Any]:
    response = client.post(
        "/api/productos",
        json={
            "nombre": name,
            "codigo_barras": barcode,
            "precio": price,
            "stock_actual": stock,
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def test_register_sale_decreases_stock(
    client: TestClient,
    admin_headers: dict[str, str],
    cashier_headers: dict[str, str],
    engine: Engine,
) -> None:
    product = create_product(
        client,
        admin_headers,
        name="Leche",
        barcode="7790000000001",
        price="1250.00",
        stock=5,
    )

    response = client.post(
        "/api/ventas",
        json={"detalles": [{"producto_id": product["id"], "cantidad": 2}]},
        headers=cashier_headers,
    )

    assert response.status_code == 201
    sale = response.json()
    assert sale["total"] == "2500.00"
    assert sale["detalles"][0]["producto_id"] == product["id"]
    assert sale["detalles"][0]["cantidad"] == 2

    history = client.get(
        "/api/ventas/historial",
        params={"limit": 1, "offset": 0},
        headers=cashier_headers,
    )
    assert history.status_code == 200
    historical_sale = history.json()[0]
    assert historical_sale["id"] == sale["id"]
    assert historical_sale["fecha"]
    assert historical_sale["cajero"] == "cajero"
    assert historical_sale["detalles"] == [
        {
            "nombre_producto": "Leche",
            "cantidad": 2,
            "subtotal": "2500.00",
        }
    ]

    product_response = client.get(
        f"/api/productos/codigo-barras/{product['codigo_barras']}",
    )
    assert product_response.status_code == 200
    assert product_response.json()["stock_actual"] == 3

    with Session(engine) as db:
        movement = db.scalar(
            select(InventoryMovementModel).where(
                InventoryMovementModel.change_type == "VENTA",
            )
        )
        assert movement is not None
        assert movement.product_id == product["id"]
        assert movement.quantity_changed == -2
        assert movement.usuario.username == "cajero"


def test_cashier_history_only_returns_their_sales(
    client: TestClient,
    admin_headers: dict[str, str],
    cashier_headers: dict[str, str],
) -> None:
    product = create_product(
        client,
        admin_headers,
        name="Fideos",
        barcode="7790000000005",
        price="500.00",
        stock=5,
    )
    second_cashier = client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "username": "cajero-dos",
            "password": "SegundoCajero123!",
            "rol": "CAJERO",
        },
    )
    assert second_cashier.status_code == 201
    second_login = client.post(
        "/api/auth/login",
        json={
            "username": "cajero-dos",
            "password": "SegundoCajero123!",
        },
    )
    assert second_login.status_code == 200
    second_cashier_headers = {
        "Authorization": f"Bearer {second_login.json()['access_token']}",
    }

    cashier_sale = client.post(
        "/api/ventas",
        headers=cashier_headers,
        json={"detalles": [{"producto_id": product["id"], "cantidad": 1}]},
    )
    second_cashier_sale = client.post(
        "/api/ventas",
        headers=second_cashier_headers,
        json={"detalles": [{"producto_id": product["id"], "cantidad": 1}]},
    )
    assert cashier_sale.status_code == second_cashier_sale.status_code == 201

    cashier_history = client.get(
        "/api/ventas/historial",
        params={"limit": 100},
        headers=cashier_headers,
    )
    assert cashier_history.status_code == 200
    cashier_sales = cashier_history.json()
    assert [sale["id"] for sale in cashier_sales] == [cashier_sale.json()["id"]]
    assert cashier_sales[0]["cajero"] == "cajero"

    admin_history = client.get(
        "/api/ventas/historial",
        params={"limit": 100},
        headers=admin_headers,
    )
    assert admin_history.status_code == 200
    assert {
        sale["id"] for sale in admin_history.json()
    } == {
        cashier_sale.json()["id"],
        second_cashier_sale.json()["id"],
    }


def test_insufficient_stock_returns_error_and_rolls_back(
    client: TestClient,
    engine: Engine,
    admin_headers: dict[str, str],
    cashier_headers: dict[str, str],
) -> None:
    first_product = create_product(
        client,
        admin_headers,
        name="Arroz",
        barcode="7790000000002",
        price="900.00",
        stock=6,
    )
    second_product = create_product(
        client,
        admin_headers,
        name="Aceite",
        barcode="7790000000003",
        price="1800.00",
        stock=1,
    )

    response = client.post(
        "/api/ventas",
        json={
            "detalles": [
                {"producto_id": first_product["id"], "cantidad": 2},
                {"producto_id": second_product["id"], "cantidad": 2},
            ]
        },
        headers=cashier_headers,
    )

    assert response.status_code == 400
    assert response.json()["code"] == "insufficient_stock"
    assert "Stock insuficiente" in response.json()["detail"]

    first_response = client.get(
        f"/api/productos/codigo-barras/{first_product['codigo_barras']}",
    )
    second_response = client.get(
        f"/api/productos/codigo-barras/{second_product['codigo_barras']}",
    )
    assert first_response.json()["stock_actual"] == 6
    assert second_response.json()["stock_actual"] == 1

    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Venta)) == 0


def test_sale_with_missing_product_returns_structured_not_found(
    client: TestClient,
    cashier_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/ventas",
        json={"detalles": [{"producto_id": 999, "cantidad": 1}]},
        headers=cashier_headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "code": "not_found",
        "detail": "No existe el producto con id 999.",
    }


def test_admin_sales_reports_aggregate_monthly_and_annual_totals(
    client: TestClient,
    engine: Engine,
    admin_headers: dict[str, str],
    cashier_headers: dict[str, str],
) -> None:
    product = create_product(
        client,
        admin_headers,
        name="Galletitas",
        barcode="7790000000004",
        price="100.00",
        stock=10,
    )
    sale_dates = [
        datetime(2026, 6, 2, 12, tzinfo=timezone.utc),
        datetime(2026, 6, 18, 15, tzinfo=timezone.utc),
        datetime(2026, 7, 4, 9, tzinfo=timezone.utc),
    ]
    for quantity in (2, 1, 1):
        response = client.post(
            "/api/ventas",
            json={
                "detalles": [
                    {"producto_id": product["id"], "cantidad": quantity}
                ]
            },
            headers=cashier_headers,
        )
        assert response.status_code == 201

    with Session(engine) as db:
        sales = db.scalars(select(Venta).order_by(Venta.id)).all()
        for sale, sale_date in zip(sales, sale_dates, strict=True):
            sale.fecha = sale_date
        db.commit()

    first_page = client.get(
        "/api/ventas/historial",
        params={"limit": 1, "offset": 0},
        headers=admin_headers,
    )
    second_page = client.get(
        "/api/ventas/historial",
        params={"limit": 1, "offset": 1},
        headers=admin_headers,
    )
    assert first_page.status_code == 200
    assert second_page.status_code == 200
    assert len(first_page.json()) == len(second_page.json()) == 1
    assert first_page.json()[0]["id"] != second_page.json()[0]["id"]

    monthly = client.get(
        "/api/ventas/reportes/mensual",
        params={"anio": 2026, "mes": 6},
        headers=admin_headers,
    )
    assert monthly.status_code == 200
    assert monthly.json() == {
        "anio": 2026,
        "mes": 6,
        "total": "300.00",
        "cantidad_ventas": 2,
    }

    annual = client.get(
        "/api/ventas/reportes/anual",
        params={"anio": 2026},
        headers=admin_headers,
    )
    assert annual.status_code == 200
    annual_months = annual.json()["meses"]
    assert len(annual_months) == 12
    assert annual_months[5] == {
        "mes": 6,
        "total": "300.00",
        "cantidad_ventas": 2,
    }
    assert annual_months[6] == {
        "mes": 7,
        "total": "100.00",
        "cantidad_ventas": 1,
    }
    assert annual_months[0] == {
        "mes": 1,
        "total": "0.00",
        "cantidad_ventas": 0,
    }

    forbidden = client.get(
        "/api/ventas/reportes/anual",
        params={"anio": 2026},
        headers=cashier_headers,
    )
    assert forbidden.status_code == 403
