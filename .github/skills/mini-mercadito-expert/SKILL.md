---
name: mini-mercadito-expert
description: Aplica siempre el contexto, las reglas de negocio y las restricciones del POS Mini Mercadito a cualquier tarea de este repositorio.
---

# Mini Mercadito Expert

Usa esta skill para toda tarea en este repositorio. Antes de proponer cambios estructurales, lee el `AGENTS.md` de la raíz y confirma que las rutas, interfaces y comandos siguen coincidiendo con el código actual.

## Contexto técnico

- Backend: Python, FastAPI, SQLAlchemy, Pydantic v2, JWT y Uvicorn.
- Base de datos: PostgreSQL 16 UTF-8; cambios de esquema versionados con Alembic.
- Frontend: Vite y Vanilla JavaScript modular; no introducir React ni otro framework pesado sin solicitud explícita.
- Desarrollo en Windows con contenedores Linux, orquestados por Docker Compose. Mantén finales de línea LF en scripts `.sh`.
- Backend separado por modelos, esquemas, routers, servicios y repositorios. No concentres lógica en `main.py`.

## Reglas de negocio obligatorias

- Roles canónicos en mayúsculas: `ADMIN`, `REPOSITOR`, `CAJERO`.
- `ADMIN`: gestión de usuarios e inventario, caja, reportes y acceso global autorizado.
- `ADMIN` y `REPOSITOR`: altas, cambios, ajustes de stock e historial de inventario.
- `ADMIN` y `CAJERO`: ventas; el cajero solo consulta su propio historial. Los reportes son exclusivos de `ADMIN`.
- Aplica RBAC en backend con dependencias `Depends`; la visibilidad de UI nunca reemplaza la autorización de API.
- Productos y usuarios nunca se borran físicamente. El `DELETE` lógico cambia `activo` a `False`; conserva ventas, detalles y auditorías. Las bajas de producto se registran en el historial.
- Impide la autodesactivación del administrador y que este se quite su propio rol. No expongas contraseñas hash.
- Mantén invariantes: precio > 0, stock >= 0 y cantidad de venta > 0. Ventas, descuento de stock y movimientos de auditoría deben ser atómicos; conserva bloqueos transaccionales para evitar sobreventa.
- Valida entradas y respuestas con esquemas Pydantic separados de ORM; maneja errores con códigos HTTP adecuados y mensajes claros en español.

## Límites de alcance y seguridad

- No implementar escáner móvil por cámara/companion, túneles externos ni infraestructura local de certificados SSL/CA. La búsqueda de productos por código de barras existente sí se conserva.
- Nunca leer, imprimir, inspeccionar, modificar ni solicitar archivos `.env` o secretos. No incluir credenciales, tokens ni valores secretos en respuestas, logs o cambios. `.env.example` es la plantilla no sensible.
- No guardar secretos en el repositorio. Usar permisos backend para seguridad; no confiar en validaciones solo frontend.

## Cambios y verificación

- Mantén cambios quirúrgicos y sigue los patrones existentes; consulta el código actual antes de asumir contratos.
- Para modelos o rutas, actualiza esquemas, migraciones Alembic y pruebas relevantes. No edites migraciones aplicadas: crea una revisión nueva.
- Añade o ajusta pruebas de integración para RBAC, validación, baja lógica, transacciones y auditoría según el cambio.
- Comandos habituales: `docker compose up -d --build`; backend `pytest`, `alembic current`, `alembic upgrade head`; frontend `npm ci` y `npm run build`.
- No uses `docker compose down -v` salvo petición explícita de borrar los datos persistentes.
