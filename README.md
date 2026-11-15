# Mini Mercadito

Mini Mercadito es un sistema modular de punto de venta (POS) e inventario para
un pequeño comercio. Permite registrar ventas, controlar existencias y
administrar usuarios con permisos por rol. La aplicación se ejecuta localmente
con Docker Compose y utiliza PostgreSQL como base de datos.

## Características

- **Autenticación JWT y RBAC:** roles `ADMIN`, `CAJERO` y `REPOSITOR`, con
  permisos verificados también en el backend.
- **Historial de ventas aislado por usuario:** cada cajero consulta únicamente
  sus ventas; `ADMIN` puede consultar el historial global.
- **Caja e inventario:** búsqueda de productos, registro transaccional de
  ventas, validación de stock y administración de productos para `ADMIN` y
  `REPOSITOR`.
- **Auditoría de inventario:** historial de altas, cambios de stock,
  reposiciones y ventas, con usuario responsable y acceso compartido para
  `ADMIN` y `REPOSITOR`.
- **Gestión de usuarios:** `ADMIN` puede crear usuarios y desactivar cuentas.
- **Reportes financieros:** resúmenes mensuales y anuales, disponibles para
  `ADMIN`. Los periodos de los reportes se calculan en UTC.
- **Errores centralizados:** respuestas de error estructuradas y mensajes en
  español para los errores de dominio de la API.
- **Migraciones de base de datos:** Alembic aplica las migraciones al iniciar
  el contenedor del backend.

## Tecnologías

| Área | Tecnologías |
| --- | --- |
| Backend | Python 3.11+ (3.12 en Docker), FastAPI, SQLAlchemy, Pydantic |
| Base de datos | PostgreSQL 16, UTF-8 |
| Migraciones y pruebas | Alembic, pytest, HTTPX |
| Frontend | Vite, JavaScript modular (Vanilla JS) |
| Entorno | Docker, Docker Compose |

## Requisitos

- Docker Desktop o Docker Engine con Docker Compose v2 (`docker compose`).
- Git para clonar el repositorio.
- Python 3.11+ opcional, solo para generar valores aleatorios o ejecutar
  pruebas fuera de Docker.

## Instalación y ejecución con Docker Compose

1. **Clona el repositorio y entra al directorio del proyecto:**

   ```sh
   git clone <URL_DEL_REPOSITORIO>
   cd minimercadito
   ```

2. **Crea el archivo local de variables de entorno:**

   En PowerShell:

   ```powershell
   Copy-Item .env.example .env
   ```

   En macOS o Linux:

   ```sh
   cp .env.example .env
   ```

   Edita `.env` y reemplaza los valores de ejemplo. En particular:

   - `POSTGRES_USER` y `POSTGRES_DB` definen el usuario y la base de datos.
   - `POSTGRES_PASSWORD` debe ser aleatoria y URL-safe porque Compose la
     incorpora en `DATABASE_URL`.
   - `JWT_SECRET_KEY` debe ser un secreto aleatorio de **al menos 32
     caracteres**.
   - `POSTGRES_PORT` define el puerto de PostgreSQL en el equipo; usa, por
     ejemplo, `5433` si el puerto `5432` ya está ocupado.

   Puedes generar valores aleatorios distintos con Python:

   ```sh
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

   Usa un valor generado para `POSTGRES_PASSWORD` y genera otro para
   `JWT_SECRET_KEY`:

   ```sh
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

   No compartas ni subas `.env` al repositorio. Está excluido por `.gitignore`.
   Compose construye `DATABASE_URL` usando las credenciales de PostgreSQL y el
   nombre del servicio `db`; no hace falta definirla manualmente en `.env`.

3. **Construye e inicia los servicios:**

   ```sh
   docker compose up -d --build
   ```

   Compose inicia PostgreSQL 16, espera a que pase su healthcheck y luego inicia
   la API y Vite. El backend aplica las migraciones de Alembic antes de arrancar
   FastAPI.

4. **Crea el primer administrador:**

   ```sh
   docker compose exec backend python -m app.cli create-user --username admin --role ADMIN
   ```

   El CLI solicita la contraseña dos veces de forma interactiva; debe tener al
   menos 12 caracteres. La contraseña no se pasa como argumento ni se almacena
   en texto plano.

5. **Abre la aplicación:**

   - Frontend: <http://localhost:5173>
   - API y documentación interactiva: <http://localhost:8000/docs>
   - PostgreSQL: `localhost:${POSTGRES_PORT}` (por defecto, `localhost:5432`)

   Inicia sesión con el usuario `admin` que acabas de crear.    Desde la sección **Usuarios**, un administrador puede dar de alta cuentas
   `CAJERO`, `REPOSITOR` u otros `ADMIN`.

### Comandos útiles

```sh
# Consultar el estado de los servicios
docker compose ps

# Seguir los registros
docker compose logs -f

# Detener los servicios y conservar la base de datos
docker compose down
```

Los datos de PostgreSQL se conservan en el volumen `postgres_data`. **No uses
`docker compose down -v` salvo que quieras eliminar permanentemente esos datos.**

## Roles y credenciales de prueba

En un entorno normal no se crean cuentas ni contraseñas predeterminadas. Crea
el primer `ADMIN` con el CLI después de iniciar Compose.

| Rol | Acceso |
| --- | --- |
| `ADMIN` | Inventario, gestión de usuarios, historial global y reportes mensuales/anuales. También puede operar la caja. |
| `CAJERO` | Punto de venta e historial de sus propias ventas. No puede administrar usuarios ni consultar reportes financieros. |
| `REPOSITOR` | Alta y actualización de productos, además del historial global de movimientos de inventario. No puede operar la caja ni administrar usuarios. |

Las siguientes cuentas existen **solo en las pruebas automatizadas** de
`backend/tests/conftest.py`; no se crean en Docker ni deben usarse en producción:

| Usuario | Contraseña | Rol |
| --- | --- | --- |
| `admin` | `AdminTestPass123` | `ADMIN` |
| `cajero` | `CajeroTestPass123` | `CAJERO` |

## API principal

| Método | Ruta | Acceso |
| --- | --- | --- |
| `POST` | `/api/auth/login` | Público |
| `GET` | `/api/productos` | Público |
| `POST`, `PUT` | `/api/productos`, `/api/productos/{product_id}` | `ADMIN`, `REPOSITOR` |
| `GET` | `/api/inventario/historial?limit=50&offset=0` | `ADMIN`, `REPOSITOR` |
| `POST` | `/api/ventas` | `ADMIN`, `CAJERO` |
| `GET` | `/api/ventas/historial?limit=50&offset=0` | `ADMIN`, `CAJERO`; el cajero ve solo sus ventas |
| `GET` | `/api/ventas/reportes/mensual?anio=2026&mes=6` | `ADMIN` |
| `GET` | `/api/ventas/reportes/anual?anio=2026` | `ADMIN` |
| `GET`, `POST` | `/api/users` | `ADMIN` |
| `DELETE` | `/api/users/{user_id}` | `ADMIN`; desactiva la cuenta |

## Estructura del repositorio

```text
.
├── backend/
│   ├── app/
│   │   ├── api/             # Dependencias de autenticación y autorización
│   │   ├── core/            # Configuración, base de datos y excepciones
│   │   ├── models/          # Modelos ORM
│   │   ├── repositories/    # Acceso a datos
│   │   ├── routers/         # Rutas de la API
│   │   ├── schemas/         # Esquemas Pydantic
│   │   ├── services/        # Lógica de negocio
│   │   └── cli.py           # Aprovisionamiento inicial de usuarios
│   ├── alembic/             # Configuración y versiones de migraciones
│   ├── tests/               # Pruebas de API y lógica de ventas
│   ├── Dockerfile
│   └── requirements*.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # Caja, inventario, usuarios e informes
│   │   ├── services/        # Cliente API y formato de datos
│   │   ├── main.js          # Estado principal y navegación por rol
│   │   └── style.css
│   ├── Dockerfile
│   └── package.json
├── .env.example             # Plantilla sin secretos
├── .gitignore
├── docker-compose.yml
└── README.md
```

El backend separa modelos, validación, rutas y lógica de negocio. El frontend
usa componentes JavaScript y servicios HTTP modulares; Vite reenvía `/api` al
servicio `backend` dentro de la red de Compose.

## Pruebas del backend

Las pruebas usan SQLite en memoria y HTTPX; no requieren una instancia de
PostgreSQL:

```sh
cd backend
python -m venv venv
```

Activa el entorno virtual y luego instala las dependencias de desarrollo:

```sh
# PowerShell
.\venv\Scripts\Activate.ps1

# macOS/Linux
source venv/bin/activate

pip install -r requirements-dev.txt
pytest
```

Las pruebas generan sus propias cuentas temporales y usan un secreto JWT
exclusivo de test.
