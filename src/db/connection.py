"""
  This is the db connection module for the application.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from core.config import settings

# Create the async engine.
# pool_size=5 keeps us safely within Supabase's strict direct connection limits!
engine = create_async_engine(settings.SUPABASE_DATABASE_URL, echo=False, pool_size=5, max_overflow=10)

# Session factory for generating isolated database transactions
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
	async with AsyncSessionLocal() as session:
		try:
			yield session
		finally:
			await session.close()
