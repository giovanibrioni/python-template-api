from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.database import engine
from app.core.logging import setup_logging
from app.core.middleware import RequestIdMiddleware
from app.core.telemetry import setup_telemetry
from app.health.router import HealthResponse, health
from app.items.exceptions import ItemNotFoundError

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging(settings)
    setup_telemetry(app, engine, settings)
    yield
    await engine.dispose()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(RequestIdMiddleware)


@app.exception_handler(ItemNotFoundError)
async def item_not_found_handler(_request: Request, _exc: ItemNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": "Item not found"})


app.add_api_route("/health", health, methods=["GET"], response_model=HealthResponse)
app.include_router(api_router, prefix="/api/v1")
