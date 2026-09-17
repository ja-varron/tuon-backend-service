from sqlalchemy.ext.asyncio import AsyncSession
import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from schemas.auth.registration import AdminSignupRequest
from repositories import users, otp_flows
from services.auth.otp import generate_otp
from core.security import generate_password_hash
from services import message

logger = logging.getLogger(__name__)

async def register_admin(db: AsyncSession, signup_data: AdminSignupRequest, *, client_ctx: dict = None):
    """
    Registers a new admin user.
    If the email already exists but is unverified, updates the password and re-issues an OTP.
    If the email is already verified, rejects with 409 Conflict.

    Args:
        db: Database session
        signup_data: Signup data
        client_ctx: Client metadata (ip_address, user_agent) for audit logging

    Returns:
        dict: Success message
    """
    client_ctx = client_ctx or {}

    # Hashes the password
    hashed_password = generate_password_hash(signup_data.password)

    # Fetches user from the database
    existing_user = await users.get_user_by_email(db, signup_data.email)

    # Checks if the email already exists
    if existing_user:
        # If the user has already been verified, reject the signup
        if existing_user.get("confirmed_created_at") is not None:
            logger.warning(
                "Signup rejected — email already verified: %s | IP: %s | UA: %s",
                signup_data.email, client_ctx.get("ip_address"), client_ctx.get("user_agent"),
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )

        # User exists but is unverified — update password and re-issue OTP
        logger.info(
            "Re-registration for unverified email: %s | IP: %s",
            signup_data.email, client_ctx.get("ip_address"),
        )

        user_id = await users.update_user_password(db, signup_data.email, hashed_password)

        # Invalidate any stale OTP flow for this email
        await otp_flows.invalidate_otp_flow_by_email(db, signup_data.email)
        await db.commit()
    else:
        # Creates a new user record
        user_id = await users.create_user(db, signup_data.email, hashed_password)

    # Generates a short-lived OTP, saving institution_name for retrieval at verification
    otp = await generate_otp(db, signup_data.email, signup_data.institution_name, str(user_id))

    # Emails the user with OTP
    await message.send_otp_email(signup_data.email, otp)

    logger.info(
        "OTP sent for signup: %s | IP: %s | UA: %s",
        signup_data.email, client_ctx.get("ip_address"), client_ctx.get("user_agent"),
    )

    # Returns success message
    return {
        "message": "OTP sent successfully to email",
        "user_id": str(user_id),
    }
