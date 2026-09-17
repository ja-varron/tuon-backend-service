from sqlalchemy.sql.expression import text
from sqlalchemy.ext.asyncio import AsyncSession

INSTITUTIONS_TABLE = 'public.institutions'

async def create_institution(db: AsyncSession, institution_name: str):
    """
    Creates a new institution.

    Args:
        db: Database session
        institution_name: Institution name
    Returns:
        str: Institution ID
    """

    sql_statement = text(f"""
        INSERT INTO {INSTITUTIONS_TABLE} (institution_name)
        VALUES (:institution_name)
        RETURNING institution_id
    """)

    result = await db.execute(sql_statement, {'institution_name': institution_name})
    return result.scalar_one()
