from __future__ import annotations

import os
from typing import Generator

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from alm.models import GrafanaAlert

# Create SQLModel engine
engine = create_async_engine(
    os.getenv("DATABASE_URL")
    .replace("+asyncpg", "")
    .replace("postgresql", "postgresql+asyncpg")
)


# Create tables
async def init_tables(delete_tables=False):
    async with engine.begin() as conn:
        if delete_tables:
            print("Starting to delete tables")
            await conn.run_sync(GrafanaAlert.metadata.drop_all)
        await conn.run_sync(GrafanaAlert.metadata.create_all)


def get_session():
    session = AsyncSession(engine)
    return session


async def get_session_gen() -> Generator[AsyncSession, None, None]:
    async with get_session() as session:
        yield session
