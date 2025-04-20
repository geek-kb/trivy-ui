from fastapi import Request
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Awaitable
import logging

logger = logging.getLogger("app")


async def custom_http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> Response:
    logger.warning(f"HTTP error occurred: {exc.detail} (status code {exc.status_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def custom_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> Response:
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> Response:
    logger.error(f"Unhandled server error: {repr(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )
