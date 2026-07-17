from contextlib import asynccontextmanager
from time import time

from fastapi import FastAPI, Response
from fastapi.routing import APIRoute

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.search import router as search_router
from app.core.config import settings
from app.core.db import close_pool, init_db, seed_admin
from app.core.logging import setup_logging
from app.core.metrics import (
    get_metrics,
    http_request_duration_seconds,
    http_requests_total,
)
from app.core.reranker import get_model
from app.core.tracker import start_tracking, stop_tracking


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    await init_db()
    await seed_admin()
    get_model()
    start_tracking()
    yield
    stop_tracking()
    await close_pool()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)


@app.middleware("http")
async def metrics_middleware(request, call_next):
    method = request.method
    path = request.url.path
    start = time()
    response = await call_next(request)
    duration = time() - start
    status = response.status_code
    http_requests_total.labels(method=method, endpoint=path, status=status).inc()
    http_request_duration_seconds.labels(method=method, endpoint=path).observe(duration)
    return response


@app.get("/metrics")
async def metrics():
    return Response(content=get_metrics(), media_type="text/plain")


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(search_router)
app.include_router(chat_router)
