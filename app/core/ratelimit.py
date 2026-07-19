from time import time

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.db import redis_client


async def rate_limit(request: Request, calls: int = 20, period: int = 60):
    user_id = request.state.user.get("id", "anonymous") if hasattr(request.state, "user") else "anonymous"
    key = f"ratelimit:{user_id}:{request.url.path}"

    client = await redis_client()
    if client is None:
        return

    now = int(time())
    window = now // period
    window_key = f"{key}:{window}"

    count = await client.incr(window_key)
    if count == 1:
        await client.expire(window_key, period * 2)

    if count > calls:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {calls} requests per {period}s. Try again shortly.",
        )


async def rate_limit_middleware(request: Request, call_next):
    if request.url.path in ("/metrics", "/health", "/auth/login", "/auth/register"):
        return await call_next(request)

    try:
        await rate_limit(request)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
    return await call_next(request)