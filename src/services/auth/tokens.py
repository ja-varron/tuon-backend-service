"""
Token service layer.

Handles the business logic for:
  - Issuing refresh tokens on signin
  - Rotating (validating + revoking old, issuing new) on /token/refresh
  - Revoking on /signout
"""

from sqlalchemy.ext.asyncio import AsyncSession
import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from repositories import profiles as profiles_repo
from repositories import refresh_tokens as tokens_repo
from core.security import create_access_token

logger = logging.getLogger(__name__)


async def issue_refresh_token(db: AsyncSession, user_id: str) -> str:
    """
    Issues a new refresh token for the given user and persists its hash.

    Args:
        db: Database session
        user_id: Authenticated user's UUID

    Returns:
        str: Raw refresh token to send to the client.
    """
    return await tokens_repo.create_refresh_token(db, user_id)


async def rotate_token(db: AsyncSession, raw_refresh_token: str, *, client_ctx: dict = None) -> dict:
    """
    Token rotation endpoint logic.

    Validates the incoming refresh token, revokes it, issues a fresh access token,
    and issues a new refresh token (rotation = old token can never be reused).

    Args:
        db: Database session
        raw_refresh_token: The raw refresh token sent by the client
        client_ctx: Client metadata (ip_address, user_agent) for audit logging

    Returns:
        dict: New access_token and refresh_token

    Raises:
        HTTP 401 if the token is invalid, expired, or already revoked.
    """
    client_ctx = client_ctx or {}

    token_record = await tokens_repo.get_valid_refresh_token(db, raw_refresh_token)
    if not token_record:
        logger.warning(
            "Token rotation failed — invalid/expired token | IP: %s | UA: %s",
            client_ctx.get("ip_address"), client_ctx.get("user_agent"),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = str(token_record["user_id"])

    # Fetch role and institution_id for the new access token
    profile = await profiles_repo.get_profile_by_user_id(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User profile not found",
        )

    # Revoke old refresh token (one-time use)
    await tokens_repo.revoke_refresh_token(db, raw_refresh_token)

    # Issue new tokens
    new_access_token = create_access_token(
        subject=user_id,
        role=profile['role'],
        institution_id=str(profile['institution_id']),
    )
    new_refresh_token = await tokens_repo.create_refresh_token(db, user_id)

    logger.info(
        "Token rotated: user_id=%s | IP: %s | UA: %s",
        user_id, client_ctx.get("ip_address"), client_ctx.get("user_agent"),
    )

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


async def signout(db: AsyncSession, raw_refresh_token: str, *, client_ctx: dict = None) -> dict:
    """
    Revokes a single refresh token (signs the user out of one device).

    Args:
        db: Database session
        raw_refresh_token: The raw refresh token sent by the client
        client_ctx: Client metadata (ip_address, user_agent) for audit logging

    Returns:
        dict: Confirmation message

    Raises:
        HTTP 401 if the token is not found or already revoked.
    """
    client_ctx = client_ctx or {}

    revoked = await tokens_repo.revoke_refresh_token(db, raw_refresh_token)
    if not revoked:
        logger.warning(
            "Signout failed — token not found/already revoked | IP: %s | UA: %s",
            client_ctx.get("ip_address"), client_ctx.get("user_agent"),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found or already revoked",
        )

    logger.info(
        "Signout successful (single device) | IP: %s | UA: %s",
        client_ctx.get("ip_address"), client_ctx.get("user_agent"),
    )
    return {"message": "Successfully signed out"}


async def signout_all(db: AsyncSession, user_id: str, *, client_ctx: dict = None) -> dict:
    """
    Revokes all refresh tokens for a user (signs out from all devices).

    Args:
        db: Database session
        user_id: The user's UUID (from the validated JWT)
        client_ctx: Client metadata (ip_address, user_agent) for audit logging

    Returns:
        dict: Confirmation message
    """
    client_ctx = client_ctx or {}

    await tokens_repo.revoke_all_user_tokens(db, user_id)

    logger.info(
        "Signout all devices: user_id=%s | IP: %s | UA: %s",
        user_id, client_ctx.get("ip_address"), client_ctx.get("user_agent"),
    )
    return {"message": "Successfully signed out from all devices"}
