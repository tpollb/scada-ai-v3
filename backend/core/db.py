"""Асинхронный пул PostgreSQL с увеличенным timeout"""
from typing import Optional
import asyncpg
from structlog import get_logger

from config.settings import settings

log = get_logger()

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        try:
            _pool = await asyncpg.create_pool(
                dsn=settings.database_url,
                min_size=2,
                max_size=10,
                command_timeout=120,  # Увеличено с 30 до 120 секунд
            )
            log.info(
                "PostgreSQL pool created",
                host=settings.db_host,
                port=settings.db_port,
                db=settings.db_name,
                timeout=120,
            )
        except Exception as e:
            log.error(
                "Failed to create PostgreSQL pool",
                error=str(e),
                host=settings.db_host,
                port=settings.db_port,
                db=settings.db_name,
            )
            raise
    return _pool


async def close_pool():
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        log.info("PostgreSQL pool closed")


async def fetch(query: str, *args) -> list[asyncpg.Record]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(query, *args)


async def fetchrow(query: str, *args) -> Optional[asyncpg.Record]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, *args)


async def fetchval(query: str, *args):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval(query, *args)
