import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.exceptions.custom_exceptions import (
    DeepSeekException,
    RetrievalException,
)

logger = logging.getLogger(__name__)

async def deepseek_exception_handler(
    request: Request,
    exc: DeepSeekException,
):
    return JSONResponse(
        status_code=503,
        content={
            "success": False,
            "error": {
                "type": "DeepSeekException",
                "message": str(exc),
            },
        },
    )


async def retrieval_exception_handler(
    request: Request,
    exc: RetrievalException,
):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "type": "RetrievalException",
                "message": str(exc),
            },
        },
    )


async def general_exception_handler(
    request: Request,
    exc: Exception,
):
    logger.exception("Unexpected server error.")

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "type": "InternalServerError",
                "message": "An unexpected error occurred.",
            },
        },
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
):
    logger.warning(
        f"HTTP {exc.status_code}: {exc.detail}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "type": "HTTPException",
                "message": exc.detail,
            },
        },
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    logger.warning(
        "Request validation failed."
    )

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "type": "ValidationError",
                "message": "Invalid request.",
                "details": exc.errors(),
            },
        },
    )


def register_exception_handlers(app: FastAPI) -> None:

    app.add_exception_handler(
        DeepSeekException,
        deepseek_exception_handler,
    )

    app.add_exception_handler(
        RetrievalException,
        retrieval_exception_handler,
    )

    app.add_exception_handler(
        HTTPException,
        http_exception_handler,
    )

    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )

    app.add_exception_handler(
        Exception,
        general_exception_handler,
    )