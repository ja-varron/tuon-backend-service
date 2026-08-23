from sqlalchemy.orm import Session
from sqlalchemy import insert, select
from db.connection import metadata

profiles_table = metadata.tables['profiles']

def get_profile_by_user_id(db: Session, user_id: str):
    """
    Fetches a profile by user ID.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        dict: Profile data
    """
    stmt = select(profiles_table).where(profiles_table.c.user_id == user_id)
    result = db.execute(stmt).mappings().first()
    return result


def create_admin_profile(db: Session, user_id: str, email: str, institution_id: str, institution_name: str):
    """
    Creates a new admin profile.
    
    Args:
        db: Database session
        user_id: User ID
        institution_id: Institution ID
        institution_name: Institution name
        
    Returns:
        str: Profile ID
    """
    stmt = insert(profiles_table).values(
        user_id=user_id,
        email=email,
        first_name=institution_name,
        last_name="Admin        ",
        role='admin',
        institution_id=institution_id
    ).returning(profiles_table.c.user_id)
    
    result = db.execute(stmt).scalar_one()
    # No db.commit() here; transaction handled at the service layer
    return result