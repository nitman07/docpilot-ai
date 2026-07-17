from datetime import datetime, timezone

from fastapi import APIRouter
from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import ResponseHandlingException
import asyncpg
import redis.asyncio as aioredis

from app.core.config import settings

router = APIRouter(tags=["health"])


async def check_qdrant() -> dict:
    start = datetime.now(timezone.utc)
    try:
        client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            grpc_port=settings.qdrant_grpc_port,
            api_key=settings.qdrant_api_key,
            prefer_grpc=settings.qdrant_prefer_grpc,
            https=False,
        )
        collections = client.get_collections()
        duration = (datetime.now(timezone.utc) - start).total_seconds()
        return {
            "status": "ok",
            "collections": len(collections.collections),
            "latency_seconds": round(duration, 3),
        }
    except (ResponseHandlingException, Exception) as e:
        duration = (datetime.now(timezone.utc) - start).total_seconds()
        logger.warning("Qdrant health check failed", error=str(e))
        return {"status": "error", "detail": str(e), "latency_seconds": round(duration, 3)}


async def check_postgres() -> dict:
    start = datetime.now(timezone.utc)
    try:
        conn = await asyncpg.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            user=settings.postgres_user,
            password=settings.postgres_password,
            database=settings.postgres_db,
            timeout=5,
        )
        version = await conn.fetchval("SELECT version()")
        await conn.close()
        duration = (datetime.now(timezone.utc) - start).total_seconds()
        return {"status": "ok", "version": version, "latency_seconds": round(duration, 3)}
    except Exception as e:
        duration = (datetime.now(timezone.utc) - start).total_seconds()
        logger.warning("PostgreSQL health check failed", error=str(e))
        return {"status": "error", "detail": str(e), "latency_seconds": round(duration, 3)}


async def check_redis() -> dict:
    start = datetime.now(timezone.utc)
    try:
        r = aioredis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            db=settings.redis_db,
            socket_connect_timeout=5,
        )
        pong = await r.ping()
        await r.aclose()
        duration = (datetime.now(timezone.utc) - start).total_seconds()
        return {"status": "ok" if pong else "error", "latency_seconds": round(duration, 3)}
    except Exception as e:
        duration = (datetime.now(timezone.utc) - start).total_seconds()
        logger.warning("Redis health check failed", error=str(e))
        return {"status": "error", "detail": str(e), "latency_seconds": round(duration, 3)}


@router.get("/health")
async def health() -> dict:
    qdrant_status = await check_qdrant()
    pg_status = await check_postgres()
    redis_status = await check_redis()

    all_ok = all(
        s["status"] == "ok"
        for s in [qdrant_status, pg_status, redis_status]
    )

    return {
        "status": "ok" if all_ok else "degraded",
        "app": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "qdrant": qdrant_status,
            "postgres": pg_status,
            "redis": redis_status,
        },
    }
