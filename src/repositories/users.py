from sqlalchemy.orm import Session
from sqlalchemy import insert, select, update
from db.connection import metadata

# Getting the users table
users_table = metadata.tables['users']

def get_user_by_email(db: Session, email: str):
    """
    Fetches a user by email.
    
    Args:
        db: Database session
        email: Email address
        
    Returns:
        dict: User data
    """
    stmt = select(users_table).where(users_table.c.email == email)
    result = db.execute(stmt).mappings().first()
    return result


def create_user(db: Session, email: str, hashed_password: str):
    """
    Creates a new user.
    
    Args:
        db: Database session
        email: Email address
        hashed_password: Hashed password
        
    Returns:
        str: User ID
    """
    # Inserts a new user with the given email and hashed password and returns the user ID
    stmt = insert(users_table).values(
        email=email,
        encrypted_password=hashed_password
    ).returning(users_table.c.user_id)

    result = db.execute(stmt).scalar_one()
    db.commit()
    return result


def update_user_verification(db: Session, user_id: str, verified_at):
    """
    Updates the verification status of a user after OTP verification to authenticated.
    
    Args:
        db: Database session
        user_id: User ID
        verified_at: Verification timestamp
    """
    # Updates the user's verification status
    stmt = update(users_table).where(users_table.c.user_id == user_id).values(
        email_created_at=verified_at
    )
    db.execute(stmt)
