import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config.settings import settings
from app.logging_config import configure_logging
from app.middleware import RequestContextMiddleware
from app.schemas.agent import TaskRequest
from app.schemas.agent import (
    TaskRequest,
    TaskValidationResponse,
    ErrorResponse,
)

configure_logging()
logger = logging.getLogger("mnl.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("MNL agent runtime starting")
    yield
    logger.info("MNL agent runtime shutting down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Python agent runtime for MNL",
    lifespan=lifespan,
)

app.add_middleware(RequestContextMiddleware)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
):
    request_id = getattr(request.state, "request_id", None)

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "The request data is invalid.",
                "request_id": request_id,
            }
        },
    )



@app.exception_handler(Exception)
async def unexpected_error_handler(
    request: Request,
    exc: Exception,
):
    logger.error(
        "unexpected_error request_id=%s",
        getattr(request.state, "request_id", "unknown"),
        exc_info=(type(exc), exc, exc.__traceback__),
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred.",
                "request_id": getattr(
                    request.state,
                    "request_id",
                    None,
                ),
            }
        },
    )


@app.get("/")
async def root():
    return {
        "message": "Welcome to MNL Agent Runtime",
        "version": settings.app_version,
    }


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "mnl-agent-runtime",
        "environment": settings.environment,
    }


# @app.post("/api/v1/tasks/validate")
# async def validate_task(task: TaskRequest):
#     return {
#         "valid": True,
#         "task_id": task.task_id,
#         "repository_id": task.repository_id,
#     }


@app.post(
    "/api/v1/tasks/validate",
    response_model=TaskValidationResponse,
)
async def validate_task(task: TaskRequest):
    return TaskValidationResponse(
        valid=True,
        task_id=task.task_id,
        repository_id=task.repository_id,
    )
