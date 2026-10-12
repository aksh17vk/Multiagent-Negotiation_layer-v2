from fastapi import FastAPI
from app.config.settings import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Python agent runtime for MNL",
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