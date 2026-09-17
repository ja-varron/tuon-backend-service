from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from db.connection import get_db

from schemas.auth.registration import AdminSignupRequest, AdminSignupResponse
from schemas.auth.otp import OTPVerifyRequest
from schemas.auth.login import SigninRequest, SigninResponse
from schemas.auth.tokens import RefreshTokenRequest, RefreshTokenResponse, TokenPayload

from services.auth import registration, otp, login, tokens
from core.security import get_current_user
from core.limiter import limiter

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_context(request: Request) -> dict:
    """
    Extracts security-relevant client metadata from the incoming request.
    Used for audit logging across all auth endpoints.

    Returns:
        dict with ip_address and user_agent
    """
    return {
        "ip_address": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown"),
    }


@router.post("/signup", response_model=AdminSignupResponse)
@limiter.limit("5/minute")
async def signup_admin(request: Request, signup_data: AdminSignupRequest, db: AsyncSession = Depends(get_db)):
    """
    Public signup endpoint. Only creates ADMIN accounts.
    Generates an OTP and waits for verification.
    """
    client_ctx = _client_context(request)
    return await registration.register_admin(db, signup_data, client_ctx=client_ctx)


@router.post("/otp/verify")
@limiter.limit("5/minute")
async def verify_otp(request: Request, verify_data: OTPVerifyRequest, db: AsyncSession = Depends(get_db)):
    """
    Verifies the OTP and finalizes the account creation (institution + profile).
    """
    client_ctx = _client_context(request)
    return await otp.verify_otp(db, verify_data, client_ctx=client_ctx)


@router.post("/signin", response_model=SigninResponse)
@limiter.limit("10/minute")
async def signin(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """
    Authenticates the user and returns a JWT access token + refresh token.
    Works for verified admin accounts.

    Accepts OAuth2 form data (username + password) so that Swagger UI's
    Authorize button works out of the box. The 'username' field should
    contain the user's email address.
    """
    client_ctx = _client_context(request)
    signin_data = SigninRequest(email=form_data.username, password=form_data.password)
    return await login.authenticate_user(db, signin_data, client_ctx=client_ctx)


@router.post("/token/refresh", response_model=RefreshTokenResponse)
@limiter.limit("20/minute")
async def refresh_token(request: Request, payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """
    Issues a new access token using a valid refresh token.
    The old refresh token is immediately revoked (token rotation).
    This endpoint is intentionally unauthenticated — it is the recovery path
    when the access token has expired.
    """
    client_ctx = _client_context(request)
    return await tokens.rotate_token(db, payload.refresh_token, client_ctx=client_ctx)


@router.post("/signout")
@limiter.limit("10/minute")
async def signout(
    request: Request,
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Revokes the provided refresh token (signs out of one device).
    """
    client_ctx = _client_context(request)
    return await tokens.signout(db, payload.refresh_token, client_ctx=client_ctx)


@router.post("/signout/all")
@limiter.limit("5/minute")
async def signout_all(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """
    Revokes all refresh tokens for the current user (signs out of all devices).
    Requires a valid access token.
    """
    client_ctx = _client_context(request)
    return await tokens.signout_all(db, current_user.sub, client_ctx=client_ctx)
