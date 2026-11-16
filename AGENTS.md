# Mini Mercadito — contexto para desarrollo

## Arquitectura

POS local: FastAPI + SQLAlchemy + Pydantic, PostgreSQL 16, Alembic y frontend Vite con JavaScript Vanilla modular. Docker Compose levanta `db`, `backend` y `frontend`; sus puertos publicados están ligados a loopback. El backend aplica migraciones al iniciar.

## Mapa del código

- `backend/app/main.py`: aplicación, errores comunes y registro de routers.
- `backend/app/core/`: configuración, sesión SQLAlchemy, seguridad JWT y excepciones.
- `backend/app/api/deps.py`: usuario autenticado y dependencias RBAC.
- `backend/app/models/models.py`: modelos ORM; `schemas/schemas.py`: contratos y validación Pydantic.
- `backend/app/routers/`: `auth`, `productos`, `inventario`, `users`, `ventas`.
- `backend/app/services/`: lógica transaccional de productos, inventario y ventas; `repositories/product_repo.py`: consultas de productos.
- `backend/alembic/versions/`: migraciones versionadas. No modificar una migración ya aplicada; crear una nueva.
- `backend/tests/`: pruebas API y reglas de negocio; `conftest.py` prepara SQLite en memoria y usuarios de prueba.
- `frontend/src/main.js`: estado, navegación y autorización visual; `components/`: caja, formularios, inventario, usuarios, historial y reportes; `services/api.js`: `fetch`, Bearer JWT y errores.

## Roles e invariantes

- Los roles se guardan en mayúsculas: `ADMIN`, `REPOSITOR`, `CAJERO`. La autorización real siempre se aplica en FastAPI con `Depends(require_role(...))`; ocultar una pestaña en frontend no sustituye RBAC.
- `ADMIN`: usuarios, inventario, caja, reportes e historial global.
- `REPOSITOR`: alta/edición/baja lógica de productos e historial de inventario; no administra usuarios ni opera caja.
- `CAJERO`: registra ventas y consulta únicamente su propio historial. Los reportes son exclusivos de `ADMIN`. La consulta de productos es pública.
- Usuarios y productos se desactivan con `activo=False`; **nunca hacer borrado físico**. Las ventas, detalles y movimientos deben conservar su integridad y trazabilidad. La baja de producto se registra como movimiento `BAJA`.
- No permitir la autodesactivación del administrador ni quitarse a sí mismo el rol `ADMIN`. Hash de contraseñas obligatorio; nunca devolver `hashed_password`.
- Precio > 0, stock >= 0 y cantidades vendidas > 0. Registrar venta, descontar stock y crear auditoría en una transacción atómica; bloquear productos durante la actualización para evitar inconsistencias.
- Mantener esquemas Pydantic separados de ORM y rutas; usar errores de dominio/HTTP claros (401/403/404/409/422 según corresponda).

## Frontend y decisiones de alcance

- Mantener Vanilla JS modular y componentes pequeños; no introducir React u otro framework pesado sin una decisión explícita.
- El cliente API añade el JWT automáticamente. Mostrar estados de carga y errores de API; conservar la navegación por rol y no confiar en ella como mecanismo de seguridad.
- Se mantiene la búsqueda de productos por código de barras, pero **no hay escáner móvil/companion, túneles externos ni CA/certificados SSL locales complejos**. No reintroducirlos sin un requerimiento explícito; priorizar operación local sencilla.

## Comandos

```sh
# Desde la raíz
docker compose up -d --build
docker compose ps
docker compose logs -f

# Backend (desde backend/, con el entorno Python activo)
pip install -r requirements-dev.txt
pytest
alembic current
alembic revision --autogenerate -m "descripcion_del_cambio"
alembic upgrade head

# Frontend (desde frontend/)
npm ci
npm run build
```

Compose ejecuta `alembic upgrade head` al iniciar el backend. Las pruebas usan SQLite en memoria; cubrir con pruebas los cambios de rutas, roles, modelos y transacciones. No usar `docker compose down -v` salvo que se quiera borrar la base persistente.

## Seguridad y formato

- **No leer, imprimir, inspeccionar ni modificar ningún archivo `.env`**; no copiar sus secretos a logs, documentación o respuestas. Usar `.env.example` como plantilla no sensible.
- Mantener los scripts `.sh` con finales de línea **LF**.
- No guardar secretos, contraseñas ni tokens en el repositorio. Validar entradas en Pydantic y mantener los mensajes de error en español.
