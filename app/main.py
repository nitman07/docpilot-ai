from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.search import router as search_router
from app.core.config import settings
from app.core.db import close_pool, init_db, seed_admin
from app.core.logging import setup_logging
from app.core.reranker import get_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    await init_db()
    await seed_admin()
    get_model()
    yield
    await close_pool()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(search_router)
app.include_router(chat_router)
