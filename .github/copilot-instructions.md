# Instrucciones del Proyecto - Mini Mercadito

## Stack Tecnológico
- **Base de Datos:** PostgreSQL 16 (en contenedor Docker, codificación UTF-8).
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy (o psycopg3), Pydantic v2, Uvicorn.
- **Frontend:** Node.js + Vite (interfaz responsiva para caja y control de stock).
- **Contenedores:** Docker y Docker Compose.

## Reglas Obligatorias para los Agentes
1. **Arquitectura Backend:** Separa siempre los modelos de BD (`models.py`), esquemas de validación (`schemas.py`) y rutas (`routers/`). Nunca pongas toda la lógica en `main.py`.
2. **Tipado y Validación:** Usa type hints de Python y esquemas de Pydantic para todas las entradas y salidas de la API.
3. **Codificación UTF-8:** Garantiza compatibilidad con caracteres en español (tildes y ñ) tanto en PostgreSQL como en las respuestas JSON de FastAPI.
4. **Control de Contexto:** Trabaja módulo por módulo; no reescribas archivos completos si solo necesitas agregar un endpoint.

## Contexto obligatorio del repositorio
- Para cualquier tarea, consulta primero el `AGENTS.md` de la raíz y aplica la skill `.github/skills/mini-mercadito-expert/SKILL.md`.
- No abras ni modifiques archivos `.env` ni solicites secretos. Mantén los scripts `.sh` con finales de línea LF.