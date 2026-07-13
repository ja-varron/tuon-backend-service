"""
JWT (JSON Web Token) implementation for authentication.
"""

from src.dependencies import get_current_user
# pyrefly: ignore [missing-import]
from fastapi import HTTPException
from src.auth.router import router
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from src.schemas import RefreshRequest
from src.config import Settings as settings

def create_access_token(user) -> str:
  """
  Creates an access token for the given user.

  Args:
      user (dict): User data.
      
  Returns:
      str: Access token.
  """
  expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

  payload = {
    "sub": user.user_id,
    "email": user.email,
    "role": user.role,
    "type": "access",
    "exp": expire
  }

  return jwt.encode(payload, settings.jwt_secret, settings.JWT_ALGORITHM)


def create_refresh_token(user) -> str:
  """
  Creates a refresh token for the given user.

  Args:
      user (dict): User data.
      
  Returns:
      str: Refresh token.
  """
  expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

  return jwt.encode({"sub": user.user_id, "type": "refresh", "exp": expire}, settings.jwt_secret, settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
  """
  Decodes a JWT token.

  Args:
      token (str): Token to decode.
      
  Returns:
      dict: Decoded token data.
  """
  return jwt.decode(token, settings.jwt_secret, algorithms=[settings.JWT_ALGORITHM])


@router.post("/refresh")
async def refresh(body: RefreshRequest):
  """
  Refreshes the access token.

  Args:
      body (RefreshRequest): Request model for refreshing the token.
      
  Returns:
      dict: Response model for tokens.
  """
  try:
    payload = decode_token(body.refresh_token)

  except JWTError as e:
    raise HTTPException(status_code=401, detail="Invalid refresh token")

  if payload.get("type") != "refresh":
    raise HTTPException(status_code=401, detail="Wrong token type")

  # Re-fetch user — picks up any role changes since token was issued
  user = get_current_user(payload.get("sub"))
  if not user:
    raise HTTPException(status_code=401, detail="User not found")

  return {
    "access_token": create_access_token(user),
    "token_type": "bearer"
  }
