# Backend

## Configuración

Configura `DATABASE_URL` y `JWT_SECRET_KEY` en el entorno. La clave JWT debe
tener al menos 32 caracteres aleatorios; genera una con:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

No uses la clave de pruebas ni guardes secretos en el repositorio. La
aplicación valida su configuración al iniciar.

## Migraciones

Desde esta carpeta, aplica el esquema:

```powershell
alembic upgrade head
```

## Aprovisionamiento de usuarios

No hay registro público. Crea el primer administrador desde un entorno
confiable después de aplicar las migraciones; el comando solicita la contraseña
interactivamente y almacena únicamente su hash:

```powershell
python -m app.cli create-user --username admin --role ADMIN
```

Luego crea usuarios de caja con `--role CAJERO` o de reposición con
`--role REPOSITOR`. Los endpoints de productos permiten `ADMIN` y `REPOSITOR`;
las ventas permiten `ADMIN` y `CAJERO`. Un administrador autenticado puede listar y
crear usuarios en `/api/users`, además de desactivar a otros usuarios con
`DELETE /api/users/{user_id}`. La desactivación conserva el registro y bloquea
el inicio de sesión; un administrador no puede desactivarse a sí mismo.

El historial paginado de ventas está disponible para `ADMIN` y `CAJERO` en
`GET /api/ventas/historial?limit=50&offset=0`. Los reportes son exclusivos de
`ADMIN`: `GET /api/ventas/reportes/mensual?anio=2026&mes=6` y
`GET /api/ventas/reportes/anual?anio=2026`. Los periodos de reporte se calculan
en UTC; el reporte anual incluye los doce meses, también los que no tuvieron
ventas.

## Pruebas

```powershell
pip install -r requirements-dev.txt
pytest
```
