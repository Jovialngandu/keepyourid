from fastapi import FastAPI

from keepyourid.config import get_settings
from keepyourid.modules.health.router import router as health_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
)

app.include_router(
    health_router,
    prefix=settings.api_v1_prefix,
)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "message": "KeepYourID API",
        "docs": "/docs",
    }