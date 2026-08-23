from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from schemas.auth.login import SigninRequest
from repositories import users, profiles
from repositories import tokens as tokens_repo
from core.security import verify_password, create_access_token

def authenticate_user(db: Session, signin_data: SigninRequest):
    """
    Step-by-step verification for admin users before authentication.

    Args:
        db: Database session
        signin_data: SigninRequest object containing email and password

    Returns:
        dict: Dictionary containing access token and profile information
    """
    # Fetching the user by email
    user = users.get_user_by_email(db, signin_data.email)

    # Checking if the user exists
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    # Checking if the password is correct
    if not verify_password(signin_data.password, user.encrypted_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    # Checking if the user has been verified
    if user.email_created_at is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account not verified via OTP")
    
    # Checking if the profile exists
    profile = profiles.get_profile_by_user_id(db, user.user_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Profile not found")
    
    # Creating an access token
    access_token = create_access_token(
        subject=str(user.user_id),
        role=profile.role,
        institution_id=str(profile.institution_id)
    )

    # Creating a refresh token (long-lived, stored as hash in DB)
    refresh_token = tokens_repo.create_refresh_token(db, str(user.user_id))

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
