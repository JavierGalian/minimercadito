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

    product = admin_product.json()
    update_payload = {
        "nombre": product["nombre"],
        "descripcion": product["descripcion"],
        "codigo_barras": product["codigo_barras"],
        "precio": product["precio"],
        "stock_actual": 5,
    }
    update = client.put(
        f"/api/productos/{product['id']}",
        headers=repositor_headers,
        json=update_payload,
    )
    assert update.status_code == 200
    assert update.json()["stock_actual"] == 5

    second_update = client.put(
        f"/api/productos/{product['id']}",
        headers=repositor_headers,
        json={**update_payload, "stock_actual": 4},
    )
    assert second_update.status_code == 200

    history = client.get(
        "/api/inventario/historial",
        headers=repositor_headers,
    )
    assert history.status_code == 200
    movements = history.json()
    assert len(movements) == 4
    assert movements[0]["change_type"] == "ACTUALIZACION"
    assert movements[0]["quantity_changed"] == -1
    assert movements[1]["change_type"] == "REPOSICION"
    assert movements[1]["quantity_changed"] == 3
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
