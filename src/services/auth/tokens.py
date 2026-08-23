"""
Token service layer.

Handles the business logic for:
  - Issuing refresh tokens on signin
  - Rotating (validating + revoking old, issuing new) on /token/refresh
  - Revoking on /signout
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from repositories import users as users_repo, profiles as profiles_repo
from repositories import tokens as tokens_repo
from core.security import create_access_token


def issue_refresh_token(db: Session, user_id: str) -> str:
    """
    Issues a new refresh token for the given user and persists its hash.

    Args:
        db: Database session
        user_id: Authenticated user's UUID

    Returns:
        str: Raw refresh token to send to the client.
    """
    return tokens_repo.create_refresh_token(db, user_id)


def rotate_token(db: Session, raw_refresh_token: str) -> dict:
    """
    Token rotation endpoint logic.

    Validates the incoming refresh token, revokes it, issues a fresh access token,
    and issues a new refresh token (rotation = old token can never be reused).

    Args:
        db: Database session
        raw_refresh_token: The raw refresh token sent by the client

    Returns:
        dict: New access_token and refresh_token

    Raises:
        HTTP 401 if the token is invalid, expired, or already revoked.
    """
    token_record = tokens_repo.get_valid_refresh_token(db, raw_refresh_token)
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = str(token_record["user_id"])

    # Fetch role and institution_id for the new access token
    profile = profiles_repo.get_profile_by_user_id(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User profile not found",
        )

    # Revoke old refresh token (one-time use)
    tokens_repo.revoke_refresh_token(db, raw_refresh_token)

    # Issue new tokens
    new_access_token = create_access_token(
        subject=user_id,
        role=profile.role,
        institution_id=str(profile.institution_id),
    )
    new_refresh_token = tokens_repo.create_refresh_token(db, user_id)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


def signout(db: Session, raw_refresh_token: str) -> dict:
    """
    Revokes a single refresh token (signs the user out of one device).

    Args:
        db: Database session
        raw_refresh_token: The raw refresh token sent by the client

    Returns:
        dict: Confirmation message

    Raises:
        HTTP 401 if the token is not found or already revoked.
    """
    revoked = tokens_repo.revoke_refresh_token(db, raw_refresh_token)
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found or already revoked",
        )
    return {"message": "Successfully signed out"}


def signout_all(db: Session, user_id: str) -> dict:
    """
    Revokes all refresh tokens for a user (signs out from all devices).

    Args:
        db: Database session
        user_id: The user's UUID (from the validated JWT)

    Returns:
        dict: Confirmation message
    """
    tokens_repo.revoke_all_user_tokens(db, user_id)
    return {"message": "Successfully signed out from all devices"}
