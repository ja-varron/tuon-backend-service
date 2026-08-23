from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from db.connection import get_db

from schemas.auth.registration import AdminSignupRequest, AdminSignupResponse
from schemas.auth.otp import OTPVerifyRequest, OTPVerifyResponse
from schemas.auth.login import SigninRequest, SigninResponse
from schemas.auth.tokens import RefreshTokenRequest, RefreshTokenResponse, TokenPayload

from services.auth import registration, otp, login, tokens
from core.security import get_current_user
from core.limiter import limiter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=AdminSignupResponse)
@limiter.limit("5/minute")
def signup_admin(request: Request, signup_data: AdminSignupRequest, db: Session = Depends(get_db)):
    """
    Public signup endpoint. Only creates ADMIN accounts.
    Generates an OTP and waits for verification.
    """
    return registration.register_admin(db, signup_data)


@router.post("/otp/verify")
@limiter.limit("5/minute")
def verify_otp(request: Request, verify_data: OTPVerifyRequest, db: Session = Depends(get_db)):
    """
    Verifies the OTP and finalizes the account creation (institution + profile).
    """
    return otp.verify_admin_otp(db, verify_data)


@router.post("/signin", response_model=SigninResponse)
@limiter.limit("10/minute")
def signin(request: Request, signin_data: SigninRequest, db: Session = Depends(get_db)):
    """
    Authenticates the user and returns a JWT access token + refresh token.
    Works for verified admin accounts.
    """
    return login.authenticate_user(db, signin_data)


@router.post("/token/refresh", response_model=RefreshTokenResponse)
@limiter.limit("20/minute")
def refresh_token(request: Request, payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Issues a new access token using a valid refresh token.
    The old refresh token is immediately revoked (token rotation).
    This endpoint is intentionally unauthenticated — it is the recovery path
    when the access token has expired.
    """
    return tokens.rotate_token(db, payload.refresh_token)


@router.post("/signout")
def signout(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """
    Revokes the provided refresh token (signs out of one device).
    Requires a valid access token to prevent anonymous token revocation.
    """
    return tokens.signout(db, payload.refresh_token)


@router.post("/signout/all")
def signout_all(
    db: Session = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """
    Revokes all refresh tokens for the current user (signs out of all devices).
    Requires a valid access token.
    """
    return tokens.signout_all(db, current_user.sub)
