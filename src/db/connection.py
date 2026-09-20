"""
  This is the db connection module for the application.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from core.config import settings

# Create the async engine.
# pool_size=5 keeps us safely within Supabase's strict direct connection limits!
auth_engine = create_async_engine(settings.SUPABASE_AUTH_URL, echo=False, pool_size=5, max_overflow=10)

api_engine = create_async_engine(settings.SUPABASE_DATABASE_URL, echo=False, pool_size=5, max_overflow=10)

AuthSessionLocal = async_sessionmaker(bind=auth_engine, expire_on_commit=False, class_=AsyncSession)

# Session factory for generating isolated database transactions
PublicSessionLocal = async_sessionmaker(bind=api_engine, expire_on_commit=False, class_=AsyncSession)


async def get_auth_db() -> AsyncGenerator[AsyncSession, None]:
	async with AuthSessionLocal() as session:
		try:
			yield session
		finally:
			await session.close()


async def get_public_db() -> AsyncGenerator[AsyncSession, None]:
	async with PublicSessionLocal() as session:
		try:
			yield session
		finally:
			await session.close()
