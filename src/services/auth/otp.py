from datetime import timezone
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import random
import string
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from core.config import settings
from core.security import verify_otp_hash, generate_otp_hash
from repositories import otp_flows, users, institutions, profiles
from schemas.auth.otp import OTPVerifyRequest

logger = logging.getLogger(__name__)

async def generate_otp(db: AsyncSession, email: str, institution_name: str, user_id: str) -> str:
    """
    Generates an OTP for the given email address.

    Args:
        db: Database session
        email: Email address
        institution_name: Institution name submitted at signup
        user_id: User ID

    Returns:
        str: OTP code
    """
    # Generates a random 6-digit OTP
    otp_code = ''.join(random.choices(string.digits, k=6))

    # Hashes the OTP
    otp_hash = generate_otp_hash(otp_code)

    # Sets the expiration time for the OTP
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

    # Creates the OTP flow in the database, storing institution_name for later retrieval
    await otp_flows.create_otp_flow(db, email, institution_name, otp_hash, expires_at, user_id)
    return otp_code


async def verify_otp(db: AsyncSession, verify_data: OTPVerifyRequest, *, client_ctx: dict = None):
    """
    Verifies the OTP and finalizes the account creation or updates the password.

    Args:
        db: Database session
        verify_data: OTP verification data
        client_ctx: Client metadata (ip_address, user_agent) for audit logging

    Returns:
        dict: Success message
    """
    client_ctx = client_ctx or {}

    # Retrieves the OTP flow
    flow = await otp_flows.get_active_otp_flow(db, verify_data.email)

    # Checks if the OTP flow is valid
    if not flow:
        logger.warning(
            "OTP verify failed — no active flow: %s | IP: %s",
            verify_data.email, client_ctx.get("ip_address"),
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active OTP flow found or OTP expired")

    # Checks if the OTP has reached the maximum number of attempts
    if flow['attempts'] >= settings.OTP_MAX_ATTEMPTS:
        await otp_flows.invalidate_otp_flow(db, flow.otp_flow_id)
        await db.commit()
        logger.warning(
            "OTP max attempts reached: %s | IP: %s | UA: %s",
            verify_data.email, client_ctx.get("ip_address"), client_ctx.get("user_agent"),
        )
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Max OTP attempts reached")

    # Checks if the OTP is valid
    if not verify_otp_hash(verify_data.otp, flow.otp_hash):
        await otp_flows.increment_attempts(db, flow.otp_flow_id)
        logger.warning(
            "OTP verify failed — wrong code: %s (attempt %d) | IP: %s",
            verify_data.email, flow['attempts'] + 1, client_ctx.get("ip_address"),
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP")

    # Valid OTP — retrieve institution_name that was saved at signup time
    try:
        # Invalidate OTP flow
        await otp_flows.invalidate_otp_flow(db, flow.otp_flow_id)

        # Set email_created_at
        verified_at = datetime.now(timezone.utc)
        user = await users.get_user_by_email(db, verify_data.email)

        # Guard: user should always exist at this point, but handle defensively
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found")

        await users.update_user_verification(db, user.user_id, verified_at)

        # Read institution_name directly from the stored OTP flow row
        institution_name = flow.institution_name

        institution_id = await institutions.create_institution(db, institution_name)
        await profiles.create_admin_profile(db, user.user_id, user.email, institution_id, institution_name)

        await db.commit()

        logger.info(
            "OTP verified — account created: %s user_id=%s | IP: %s | UA: %s",
            verify_data.email, user.user_id,
            client_ctx.get("ip_address"), client_ctx.get("user_agent"),
        )

        return {"message": "OTP verified successfully. Admin account created."}
    except HTTPException:
        # Re-raise HTTP exceptions (e.g. the 404 above) without overriding them
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Failed to finalize account creation for %s: %s", verify_data.email, e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to finalize account creation")
