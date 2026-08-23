from sqlalchemy.orm import Session
from sqlalchemy import insert, select, update
from datetime import datetime
from db.connection import metadata

# OTP flows table
otp_flows_table = metadata.tables['otp_flows']

def create_otp_flow(db: Session, email: str, institution_name: str, otp_hash: str, expires_at: datetime, user_id: str):
    """
    Creates a new OTP flow.
    
    Args:
        db: Database session
        email: Email address
        institution_name: Institution name submitted at signup
        otp_hash: Hashed OTP
        expires_at: Expiration timestamp
        user_id: User ID associated with the flow
        
    Returns:
        str: OTP flow ID
    """
    # Inserts a new OTP flow into the database
    stmt = insert(otp_flows_table).values(
        email=email,
        user_id=user_id,
        institution_name=institution_name,
        otp_hash=otp_hash,
        expires_at=expires_at,
        attempts=0,
        is_active=True
    ).returning(otp_flows_table.c.otp_flow_id)
    
    # Executes the statement and returns the OTP flow ID
    result = db.execute(stmt).scalar_one()
    
    # Commits the transaction
    db.commit()

    return result


def get_active_otp_flow(db: Session, email: str):
    """
    Fetches an active OTP flow.
    
    Args:
        db: Database session
        email: Email address
        
    Returns:
        dict: OTP flow data
    """

    # Selects the OTP flow from the database based on the email address,
    # whether it is active, and whether it has expired
    stmt = select(otp_flows_table).where(
        otp_flows_table.c.email == email,
        otp_flows_table.c.is_active == True,
        otp_flows_table.c.expires_at > datetime.utcnow()
    )
    
    # Executes the statement and returns the OTP flow data
    result = db.execute(stmt).mappings().first()
    return result


def increment_attempts(db: Session, flow_id: str):
    """
    Increments the attempts of an OTP flow if the input OTP is incorrect.
    
    Args:
        db: Database session    
        flow_id: OTP flow ID
    """

    # Updates the OTP flow with an incremented attempts count
    stmt = update(otp_flows_table).where(otp_flows_table.c.otp_flow_id == flow_id).values(
        attempts=otp_flows_table.c.attempts + 1
    )
    
    # Executes the statement
    db.execute(stmt)
    
    # Commits the transaction
    db.commit()


def invalidate_otp_flow(db: Session, flow_id: str):
    """
    Invalidates an OTP flow.
    
    Args:
        db: Database session
        flow_id: OTP flow ID
    """

    # Updates the OTP flow to be inactive
    stmt = update(otp_flows_table).where(otp_flows_table.c.otp_flow_id == flow_id).values(
        is_active=False
    )
    
    # Executes the statement
    db.execute(stmt)
    
    # Not committing here because it might be part of a transaction
