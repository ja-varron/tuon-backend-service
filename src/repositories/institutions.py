from sqlalchemy.orm import Session
from sqlalchemy import insert
from db.connection import metadata

institutions_table = metadata.tables['institutions']

def create_institution(db: Session, institution_name: str, user_id: str):
    """
    Creates a new institution.
    
    Args:
        db: Database session
        institution_name: Institution name
        
    Returns:
        str: Institution ID
    """
    stmt = insert(institutions_table).values(
        institution_name=institution_name,
        created_by=user_id
    ).returning(institutions_table.c.institution_id)
    
    # Executes the statement and returns the institution ID
    result = db.execute(stmt).scalar_one()
    
    return result
