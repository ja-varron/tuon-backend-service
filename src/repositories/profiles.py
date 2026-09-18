from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from sqlalchemy import text

PROFILES_TABLE = 'public.profiles'

async def get_profile_by_user_id(db: AsyncSession, user_id: str):
    """
    Fetches a profile by user ID.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        dict: User data
    """
    sql_statement = text(f"SELECT * FROM {PROFILES_TABLE} WHERE user_id = :user_id")

    result = await db.execute(sql_statement, {'user_id': user_id})
    return result.mappings().first()



async def create_admin_profile(db: AsyncSession, user_id: str, email: str, institution_id: str, institution_name: str):
    """
    Creates a new admin profile.

    Args:
        db: Database session
        user_id: User ID
        institution_id: Institution ID
        institution_name: Institution name
    """

    sql_statement = text(f"""
        INSERT INTO {PROFILES_TABLE} (user_id, email, first_name, last_name, role, institution_id)
        VALUES (:user_id, :email, :first_name, :last_name, :role, :institution_id)
    """)

    await db.execute(sql_statement, {
        'user_id': user_id,
        'email': email,
        'first_name': institution_name,
        'last_name': 'Admin',
        'role': 'admin',
        'institution_id': institution_id
    })
    # await db.commit()  # Commit the transaction; transaction handled at the service layer
    # return result.mappings().first()['user_id']


async def create_profile(db: AsyncSession, user_id: str, email: str, first_name: str, middle_name: str, last_name: str, role: str, institution_id: str):
    """
    Creates a new profile.

    Args:
        db: Database session
        user_id: User ID
        email: User email
        first_name: User first name
        last_name: User last name
        role: User role
        institution_id: Institution ID
    """

    sql_statement = text(f"""
        INSERT INTO {PROFILES_TABLE} (user_id, email, first_name, middle_name, last_name, role, institution_id)
        VALUES (:user_id, :email, :first_name, :middle_name, :last_name, :role, :institution_id)
    """)

    await db.execute(sql_statement, {
        'user_id': user_id,
        'email': email,
        'first_name': first_name,
        'middle_name': middle_name,
        'last_name': last_name,
        'role': role,
        'institution_id': institution_id
    })


async def update_profile(db: AsyncSession, user_id: str, first_name: str, middle_name: str, last_name: str):
    """
    Updates an existing profile.

    Args:
        db: Database session
        user_id: User ID
        first_name: User first name
        middle_name: User middle name
        last_name: User last name
    """

    sql_statement = text(f"""
        UPDATE {PROFILES_TABLE}
        SET first_name = :first_name,
            middle_name = :middle_name,
            last_name = :last_name,
            updated_at = now()
        WHERE user_id = :user_id
    """)

    await db.execute(sql_statement, {
        'user_id': user_id,
        'first_name': first_name,
        'middle_name': middle_name,
        'last_name': last_name
    })