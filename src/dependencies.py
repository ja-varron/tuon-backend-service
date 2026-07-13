# pyrefly: ignore [missing-import]
from fastapi import Depends, HTTPException
# pyrefly: ignore [missing-import]
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Callable
from jose import JWTError 
from src.auth.jwt import decode_token

bearer = HTTPBearer()

async def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)):
  """
  Dependency to get the currently authenticated user from a JWT token in the Authorization header.
  
  It verifies the token, checks if it's an access token, and returns a dictionary with user information.
  
  Args:
    creds: The HTTPAuthorizationCredentials object from the request headers.
  
  Returns:
    A dictionary with the user's ID, email, and role.
  
  Raises:
    HTTPException: If the token is invalid, not an access token, or missing.
  """

  try:
    payload = decode_token(creds.credentials)
  except JWTError:
    raise HTTPException(401, "invalid_token", headers={"WWW-Authenticate": "Bearer"})

  if payload.get("type") != "access":
    raise HTTPException(401, "wrong_token_type")
  
  return {
    "id": payload["sub"],
    "email": payload["email"],
    "role": payload.get("role", "user")
  }


def require_role(*roles: str) -> Callable:
  """
  Returns a dependency that checks if the current user has one of the specified roles.

  Usage: Depends(require_role('admin', 'moderator'))
  
  Args:
    *roles: The roles to check for (e.g., "admin", "user").
  
  Returns:
    A dependency function that can be used with FastAPI's Depends().
  
  Raises:
    HTTPException: If the user is not authenticated or does not have any of the required roles.
  """

  async def checker(user=Depends(get_current_user)):
    if user["role"] not in roles:
      raise HTTPException(403, "forbidden")
    return user
  
  return checker


def require_scope(scope: str) -> Callable:
  """
  Returns a dependency that checks if the current user has the specified scope.

  Usage: Depends(require_scope('user_read'))
  
  Args:
    scope: The scope to check for (e.g., "user_read").
  
  Returns:
    A dependency function that can be used with FastAPI's Depends().
  
  Raises:
    HTTPException: If the user is not authenticated or does not have the required scope.
  """

  async def checker(user=Depends(get_current_user)):
    if scope not in user.get("scopes", []):
      raise HTTPException(403, "forbidden")
    return user
  return checker
  