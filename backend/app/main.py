from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import get_settings
from .core.exceptions import ApplicationError
from .routers import auth, inventario, productos, users, ventas


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    get_settings()
    yield


app = FastAPI(title="Mini Mercadito API", lifespan=lifespan)


@app.exception_handler(ApplicationError)
async def application_error_handler(
    request: Request,
    exc: ApplicationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "detail": exc.detail,
        },
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["Autenticación"],
)
app.include_router(
    productos.router,
    prefix="/api/productos",
    tags=["Productos"],
)
app.include_router(
    inventario.router,
    prefix="/api/inventario",
    tags=["Inventario"],
)
app.include_router(
    ventas.router,
    prefix="/api/ventas",
    tags=["Ventas"],
)
app.include_router(
    users.router,
    prefix="/api/users",
    tags=["Usuarios"],
)
