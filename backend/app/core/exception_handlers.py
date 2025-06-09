from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger("app")


async def custom_http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    logger.warning(f"HTTP error occurred: {exc.detail} (status code {exc.status_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def custom_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    client_host = request.client.host if request.client else "Unknown"
    logger.error(
        f"Unhandled server error on {request.method} {request.url.path}\n"
        f"Client Host: {client_host}\n"
        f"Exception: {exc.__class__.__name__}: {str(exc)}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )
