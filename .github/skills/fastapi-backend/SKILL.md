---
name: fastapi-backend
description: Estándares de desarrollo para crear endpoints, modelos y esquemas en Python con FastAPI para el mini mercadito. Usar al programar rutas de productos, ventas o conexión a PostgreSQL.
---
# Skill: Desarrollo Backend con FastAPI

## Convenciones de Código
1. **Rutas:** Usa `APIRouter` con prefijos claros (ej. `/api/productos`, `/api/ventas`) y etiquetas (`tags=["Productos"]`).
2. **Validación:** Define esquemas separados para creación (`ProductoCreate`) y respuesta (`ProductoResponse` con `from_attributes = True`).
3. **Manejo de Errores:** Devuelve `HTTPException` con códigos estándar (`404` si no existe el producto, `400` si no hay stock suficiente para vender).
4. **Transacciones de Venta:** Al registrar una venta, descuenta el `stock_actual` de cada producto dentro de la misma transacción de base de datos para evitar inconsistencias.