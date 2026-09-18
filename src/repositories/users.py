from datetime import timezone
from datetime import datetime
from sqlalchemy.sql.expression import text
from sqlalchemy.ext.asyncio import AsyncSession

USERS_TABLE = 'tuon_auth.users'

async def get_user_by_email(db: AsyncSession, email: str):
    """
    Fetches a user by email.

    Args:
        db: Database session
        email: Email address

    Returns:
        dict: User data
    """
    sql_statement = text(f"""
        SELECT * FROM {USERS_TABLE} WHERE email = :email
    """)

    result = await db.execute(sql_statement, {'email': email})

    return result.mappings().first()


async def create_user(db: AsyncSession, email: str, hashed_password: str):
    """
    Creates a new user.

    Args:
        db: Database session
        email: Email address
        hashed_password: Hashed password

    Returns:
        str: User ID
    """

    sql_statement = text(f"""
        INSERT INTO {USERS_TABLE} (email, encrypted_password)
        VALUES (:email, :hashed_password)
        RETURNING user_id
    """)

    result = await db.execute(sql_statement, {'email': email, 'hashed_password': hashed_password})
    await db.commit()

    return result.mappings().first()['user_id']


async def update_user_verification(db: AsyncSession, user_id: str, verified_at):
    """
    Updates the verification status of a user after OTP verification to authenticated.

    Args:
        db: Database session
        user_id: User ID
        verified_at: Verification timestamp
    """
    # Updates the user's verification status
    sql_statement = text(f"""
        UPDATE {USERS_TABLE} SET confirmed_created_at = :verified_at WHERE user_id = :user_id
    """)

    await db.execute(sql_statement, {'verified_at': verified_at, 'user_id': user_id})
    await db.commit()



async def update_user_password(db: AsyncSession, email: str, hashed_password: str):
    """
    Updates the password for an existing user (e.g. during re-signup before verification).

    Args:
        db: Database session
        email: User's email
        hashed_password: New hashed password
    """
    sql_statement = text(f"""
        UPDATE {USERS_TABLE} SET encrypted_password = :hashed_password WHERE email = :email RETURNING user_id
    """)

    result = await db.execute(sql_statement, {'hashed_password': hashed_password, 'email': email})
    await db.commit()

    return result.mappings().first()['user_id']


async def create_user_from_admin(db: AsyncSession, email: str, hashed_password: str):
    sql_statement = text(f"""
        INSERT INTO {USERS_TABLE}
        (email, encrypted_password, confirmed_created_at)
        VALUES (:email, :hashed_password, now())
        RETURNING user_id
    """)

    result = await db.execute(
        sql_statement, 
        {'email': email, 'hashed_password': hashed_password, 'confirmed_created_at': datetime.now(timezone.utc)}
    )

    return result.mappings().first()['user_id']
