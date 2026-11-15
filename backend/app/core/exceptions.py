class ApplicationError(Exception):
    status_code = 500
    code = "application_error"

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class NotFoundError(ApplicationError):
    status_code = 404
    code = "not_found"


class InsufficientStockError(ApplicationError):
    status_code = 400
    code = "insufficient_stock"

    def __init__(self, producto_id: int, disponible: int, solicitado: int) -> None:
        super().__init__(
            f"Stock insuficiente para el producto {producto_id}: "
            f"disponible {disponible}, solicitado {solicitado}."
        )
        self.producto_id = producto_id
        self.disponible = disponible
        self.solicitado = solicitado


class ConflictError(ApplicationError):
    status_code = 409
    code = "conflict"
