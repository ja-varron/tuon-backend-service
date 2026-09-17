from datetime import timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import text
from datetime import datetime

# OTP flows table
OTP_FLOWS_TABLE = 'tuon_auth.otp_flows'

async def create_otp_flow(db: AsyncSession, email: str, institution_name: str, otp_hash: str, expires_at: datetime, user_id: str):
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
    sql_statement = text(f"""
        INSERT INTO {OTP_FLOWS_TABLE} (email, user_id, institution_name, otp_hash, expires_at)
        VALUES (:email, :user_id, :institution_name, :otp_hash, :expires_at)
        RETURNING otp_flow_id
    """)

    # Executes the statement and returns the OTP flow ID
    result = await db.execute(sql_statement, {
        'email': email,
        'user_id': user_id,
        'institution_name': institution_name,
        'otp_hash': otp_hash,
        'expires_at': expires_at
    })

    # Commits the transaction
    await db.commit()

    return result


async def get_active_otp_flow(db: AsyncSession, email: str):
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

    sql_statement = text(f"""
        SELECT * FROM {OTP_FLOWS_TABLE}
        WHERE email = :email
        AND is_active = TRUE
        AND expires_at > :now
    """)

    result = await db.execute(sql_statement, {
        'email': email,
        'now': datetime.now(timezone.utc)
    })
    return result.mappings().first()


async def increment_attempts(db: AsyncSession, flow_id: str):
    """
    Increments the attempts of an OTP flow if the input OTP is incorrect.

    Args:
        db: Database session
        flow_id: OTP flow ID
    """
    # Updates the OTP flow with an incremented attempts count
    sql_statement = text(f"""
        UPDATE {OTP_FLOWS_TABLE}
        SET attempts = attempts + 1
        WHERE otp_flow_id = :flow_id
    """)

    # Executes the statement
    await db.execute(sql_statement, {'flow_id': flow_id})

    # Commits the transaction
    await db.commit()



async def invalidate_otp_flow(db: AsyncSession, flow_id: str):
    """
    Invalidates an OTP flow.

    Args:
        db: Database session
        flow_id: OTP flow ID
    """

    # Updates the OTP flow to be inactive
    sql_statement = text(f"""
        UPDATE {OTP_FLOWS_TABLE}
        SET is_active = FALSE
        WHERE otp_flow_id = :flow_id
    """)

    # Executes the statement
    await db.execute(sql_statement, {'flow_id': flow_id})

    # Commits the transaction
    await db.commit()


async def invalidate_otp_flow_by_email(db: AsyncSession, email: str):
    """
    Invalidates all active OTP flows for a given email address.
    Used when a user re-submits signup to clear stale flows.

    Args:
        db: Database session
        email: Email address
    """

    sql_statement = text(f"""
        UPDATE {OTP_FLOWS_TABLE}
        SET is_active = FALSE
        WHERE email = :email
        AND is_active = TRUE
    """)

    await db.execute(sql_statement, {'email': email})

    # Commits the transaction
    await db.commit()
