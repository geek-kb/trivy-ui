# backend/app/core/exception_handlers.py
from fastapi import FastAPI, Request
import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response
from fastapi.exception_handlers import (
    http_exception_handler as fastapi_http_exception_handler,
    request_validation_exception_handler as fastapi_validation_exception_handler,
)

logger = logging.getLogger("app")


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> Response:
    logger.warning(f"HTTP error occurred: {exc.detail} (status code {exc.status_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def validation_exception_handler(
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
