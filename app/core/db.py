import asyncpg
from loguru import logger

from app.core.config import settings

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            host=settings.postgres_host,
            port=settings.postgres_port,
            user=settings.postgres_user,
            password=settings.postgres_password,
            database=settings.postgres_db,
            min_size=2,
            max_size=10,
        )
        logger.info("PostgreSQL pool created")
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("PostgreSQL pool closed")


INIT_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL,
    title TEXT,
    doc_metadata JSONB DEFAULT '{}',
    chunk_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'processing',
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at DESC);

CREATE TABLE IF NOT EXISTS chat_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_history_session ON chat_history(session_id, created_at);

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
"""


async def init_db() -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(INIT_SQL)
    logger.info("Database schema initialized")


async def get_chat_history(session_id: str, limit: int = 5) -> list[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT role, content FROM chat_history
               WHERE session_id = $1
               ORDER BY created_at DESC
               LIMIT $2""",
            session_id,
            limit,
        )
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


async def save_chat_turn(session_id: str, query: str, response: str) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO chat_history (session_id, role, content) VALUES ($1, 'user', $2)""",
            session_id,
            query,
        )
        await conn.execute(
            """INSERT INTO chat_history (session_id, role, content) VALUES ($1, 'assistant', $2)""",
            session_id,
            response,
        )


async def get_user_by_email(email: str) -> dict | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)
    return dict(row) if row else None


async def create_user(email: str, password_hash: str, role: str = "user") -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO users (email, password_hash, role)
               VALUES ($1, $2, $3)
               RETURNING id, email, role, created_at""",
            email, password_hash, role,
        )
    return dict(row)


async def seed_admin() -> None:
    from app.core.auth import hash_password
    existing = await get_user_by_email(settings.admin_email)
    if existing:
        return
    hashed = hash_password(settings.admin_password)
    await create_user(settings.admin_email, hashed, role="admin")
    logger.info(f"Admin user created: {settings.admin_email}")
