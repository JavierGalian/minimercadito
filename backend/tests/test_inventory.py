import re

from fastapi.testclient import TestClient


def test_repositor_can_manage_products_and_view_shared_inventory_history(
    client: TestClient,
    admin_headers: dict[str, str],
    cashier_headers: dict[str, str],
    repositor_headers: dict[str, str],
) -> None:
    admin_product = client.post(
        "/api/productos",
        headers=admin_headers,
        json={
            "nombre": "Harina",
            "descripcion": "Harina de trigo",
            "codigo_barras": "7798000000001",
            "precio": "1200.00",
            "stock_actual": 2,
        },
    )
    assert admin_product.status_code == 201
    assert admin_product.json()["creado_por"] == "admin"
    assert admin_product.json()["creado_por_id"] is not None
    assert admin_product.json()["actualizado_en"] is None

    repositor_product = client.post(
        "/api/productos",
        headers=repositor_headers,
        json={
            "nombre": "Azúcar",
            "descripcion": None,
            "codigo_barras": "7798000000002",
            "precio": "900.00",
            "stock_actual": 0,
        },
    )
    assert repositor_product.status_code == 201
    assert repositor_product.json()["creado_por"] == "repositor"

    product = admin_product.json()
    update_payload = {
        "nombre": product["nombre"],
        "descripcion": product["descripcion"],
        "codigo_barras": product["codigo_barras"],
        "precio": "1300.00",
        "stock_actual": 5,
    }
    update = client.put(
        f"/api/productos/{product['id']}",
        headers=repositor_headers,
        json=update_payload,
    )
    assert update.status_code == 200
    assert update.json()["stock_actual"] == 5
    assert update.json()["precio"] == "1300.00"

    second_update = client.put(
        f"/api/productos/{product['id']}",
        headers=repositor_headers,
        json={**update_payload, "stock_actual": 4},
    )
    assert second_update.status_code == 200

    metadata_update = client.put(
        f"/api/productos/{product['id']}",
        headers=repositor_headers,
        json={
            **update_payload,
            "descripcion": "Actualizada",
            "stock_actual": 4,
        },
    )
    assert metadata_update.status_code == 200

    product_listing = client.get("/api/productos")
    assert product_listing.status_code == 200
    updated_product = next(
        item
        for item in product_listing.json()
        if item["id"] == product["id"]
    )
    assert updated_product["creado_por"] == "admin"
    assert updated_product["actualizado_por"] == "repositor"
    assert updated_product["actualizado_por_id"] is not None
    assert updated_product["actualizado_en"] is not None

    history = client.get(
        "/api/inventario/historial",
        headers=repositor_headers,
    )
    assert history.status_code == 200
    movements = history.json()
    assert len(movements) == 5
    assert movements[0]["change_type"] == "ACTUALIZACION"
    assert movements[0]["quantity_changed"] == 0
    assert movements[1]["change_type"] == "ACTUALIZACION"
    assert movements[1]["quantity_changed"] == -1
    assert movements[2]["change_type"] == "REPOSICION"
    assert movements[2]["quantity_changed"] == 3
    assert movements[0]["username"] == "repositor"
    assert movements[0]["product_name"] == "Harina"
    assert {
        movement["username"] for movement in movements
    } == {"admin", "repositor"}

    admin_history = client.get(
        "/api/inventario/historial",
        headers=admin_headers,
    )
    assert admin_history.status_code == 200
    assert len(admin_history.json()) == len(movements)

    forbidden_history = client.get(
        "/api/inventario/historial",
        headers=cashier_headers,
    )
    forbidden_sales_history = client.get(
        "/api/ventas/historial",
        headers=repositor_headers,
    )
    forbidden_update = client.put(
        f"/api/productos/{product['id']}",
        headers=cashier_headers,
        json=update_payload,
    )
    forbidden_create = client.post(
        "/api/productos",
        headers=cashier_headers,
        json={
            "nombre": "Producto restringido",
            "precio": "100.00",
            "stock_actual": 1,
        },
    )
    assert forbidden_history.status_code == 403
    assert forbidden_sales_history.status_code == 403
    assert forbidden_update.status_code == 403
    assert forbidden_create.status_code == 403


def test_inventory_stock_update_and_deactivation_are_audited_and_role_protected(
    client: TestClient,
    admin_headers: dict[str, str],
    repositor_headers: dict[str, str],
    cashier_headers: dict[str, str],
) -> None:
    created = client.post(
        "/api/productos",
        headers=admin_headers,
        json={
            "nombre": "Lentejas",
            "codigo_barras": "7798000000099",
            "precio": "800.00",
            "stock_actual": 4,
        },
    )
    assert created.status_code == 201
    product_id = created.json()["id"]

    stock_update = client.patch(
        f"/api/productos/{product_id}/stock",
        headers=repositor_headers,
        json={"stock_actual": 9},
    )
    assert stock_update.status_code == 200
    assert stock_update.json()["stock_actual"] == 9

    forbidden_stock_update = client.patch(
        f"/api/productos/{product_id}/stock",
        headers=cashier_headers,
        json={"stock_actual": 2},
    )
    forbidden_deactivation = client.delete(
        f"/api/productos/{product_id}",
        headers=cashier_headers,
    )
    assert forbidden_stock_update.status_code == 403
    assert forbidden_deactivation.status_code == 403

    deactivated = client.delete(
        f"/api/productos/{product_id}",
        headers=repositor_headers,
    )
    assert deactivated.status_code == 204
    assert all(
        item["id"] != product_id
        for item in client.get("/api/productos").json()
    )
    assert client.get(
        "/api/productos/codigo-barras/7798000000099",
    ).status_code == 404
    assert client.patch(
        f"/api/productos/{product_id}/stock",
        headers=repositor_headers,
        json={"stock_actual": 10},
    ).status_code == 404
    assert client.post(
        "/api/ventas",
        headers=admin_headers,
        json={"detalles": [{"producto_id": product_id, "cantidad": 1}]},
    ).status_code == 404

    history = client.get(
        "/api/inventario/historial",
        headers=admin_headers,
    )
    product_movements = [
        item for item in history.json() if item["product_id"] == product_id
    ]
    assert [item["change_type"] for item in product_movements] == [
        "BAJA",
        "REPOSICION",
        "CREACION",
    ]


def test_inventory_pdf_export_is_authenticated_and_contains_active_products(
    client: TestClient,
    admin_headers: dict[str, str],
    repositor_headers: dict[str, str],
    cashier_headers: dict[str, str],
) -> None:
    active_product = client.post(
        "/api/productos",
        headers=admin_headers,
        json={
            "nombre": "Producto activo",
            "codigo_barras": "7798000000101",
            "precio": "1234.50",
            "stock_actual": 7,
        },
    )
    inactive_product = client.post(
        "/api/productos",
        headers=admin_headers,
        json={
            "nombre": "Producto dado de baja",
            "codigo_barras": "7798000000102",
            "precio": "500.00",
            "stock_actual": 3,
        },
    )
    assert active_product.status_code == 201
    assert inactive_product.status_code == 201
    assert client.delete(
        f"/api/productos/{inactive_product.json()['id']}",
        headers=admin_headers,
    ).status_code == 204

    response = client.get(
        "/api/inventory/export/pdf",
        headers=repositor_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")
    assert b"Producto activo" in response.content
    assert b"Producto dado de baja" not in response.content
    assert b"repositor" in response.content
    assert re.fullmatch(
        r'attachment; filename="inventario_\d{4}-\d{2}-\d{2}_repositor\.pdf"',
        response.headers["content-disposition"],
    )

    assert client.get("/api/inventory/export/pdf").status_code == 401
    assert client.get(
        "/api/inventory/export/pdf",
        headers=cashier_headers,
    ).status_code == 403
