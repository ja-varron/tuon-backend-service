from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

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


def get_my_profile(db: Session, user_id: str) -> dict:
    sql_statement = text(f"""
         SELECT
            p.user_id,
            p.email,
            p.first_name,
            p.middle_name,
            p.last_name,
            p.role,
            p.examinee_id_number,
            p.created_at,
            p.updated_at,
            i.institution_id,
            i.institution_name
        FROM {PROFILES_TABLE} p
        JOIN institutions i ON p.institution_id = i.institution_id
        WHERE p.user_id = :user_id
    """)

    row = db.execute(sql_statement, {'user_id': user_id}).mappings().fetchone()

    if not row:
        raise HTTPException(
            status_code=404,
            detail={
                'error': {
                    'code': 'PROFILE_NOT_FOUND',
                    'message': 'No profile found for this account'
                }
            },
        )

    return {
        'user_id': row['user_id'],
        "email": row["email"],
        "first_name": row["first_name"],
        "middle_name": row["middle_name"],
        "last_name": row["last_name"],
        "role": row["role"],
        "examinee_id_number": row["examinee_id_number"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "institution": {
            "institution_id": row["institution_id"],
            "institution_name": row["institution_name"],
        },
    }
