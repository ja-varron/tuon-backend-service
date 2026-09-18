from sqlalchemy.sql.expression import text
from sqlalchemy.ext.asyncio import AsyncSession

async def set_rls_user(db: AsyncSession, user_id: str) -> None:
    """
    Set the RLS (Row-Level Security) user for the current database session.

    Args:
        db (AsyncSession): The asynchronous database session.
        user_id (str): The user ID to set for RLS.

    Returns:
        None
    """
    rls = text(f"""
        SELECT set_config(
            'request.jwt.claim.sub',
            :user_id,
            true
        )
    """)

    await db.execute(rls, {"user_id": user_id})
    