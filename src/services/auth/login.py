from sqlalchemy.ext.asyncio import AsyncSession
import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from schemas.auth.login import SigninRequest
from repositories import users, profiles
from repositories import refresh_tokens as tokens_repo
from core.security import verify_password_hash, create_access_token

logger = logging.getLogger(__name__)

async def authenticate_user(db: AsyncSession, signin_data: SigninRequest, *, client_ctx: dict = None):
    """
    Step-by-step verification for admin users before authentication.

    Args:
        db: Database session
        signin_data: SigninRequest object containing email and password
        client_ctx: Client metadata (ip_address, user_agent) for audit logging

    Returns:
        dict: Dictionary containing access token and profile information
    """
    client_ctx = client_ctx or {}

    # Fetching the user by email
    user = await users.get_user_by_email(db, signin_data.email)

    # Checking if the user exists
    if not user:
        logger.warning(
            "Login failed — unknown email: %s | IP: %s | UA: %s",
            signin_data.email, client_ctx.get("ip_address"), client_ctx.get("user_agent"),
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Checking if the password is correct
    if not verify_password_hash(signin_data.password, user.encrypted_password):
        logger.warning(
            "Login failed — wrong password for: %s | IP: %s | UA: %s",
            signin_data.email, client_ctx.get("ip_address"), client_ctx.get("user_agent"),
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Checking if the user has been verified
    if user.confirmed_created_at is None:
        logger.warning(
            "Login failed — unverified account: %s | IP: %s",
            signin_data.email, client_ctx.get("ip_address"),
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account not verified via OTP")

    # Checking if the profile exists
    profile = await profiles.get_profile_by_user_id(db, user.user_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Profile not found")

    # Creating an access token
    access_token = create_access_token(
        subject=str(user.user_id),
        role=profile.role,
        institution_id=str(profile.institution_id)
    )

    # Creating a refresh token (long-lived, stored as hash in DB)
    refresh_token = await tokens_repo.create_refresh_token(db, str(user.user_id))

    logger.info(
        "Login successful: user_id=%s email=%s | IP: %s | UA: %s",
        user.user_id, signin_data.email,
        client_ctx.get("ip_address"), client_ctx.get("user_agent"),
    )

    # Returning the access token, refresh token, and profile information
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "profile": {
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "role": profile.role,
            "institution_id": str(profile.institution_id)
        }
    }
