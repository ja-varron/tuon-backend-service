from datetime import datetime, timedelta
from typing import Any, Callable, Union
from jose import jwt, JWTError
from argon2 import PasswordHasher
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from schemas.auth.tokens import TokenPayload

from core.config import settings

password_hasher = PasswordHasher()

# Points to signin — used by Swagger UI "Authorize" button and OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/signin")


def generate_password_hash(plain_password: str) -> str:
    """
    Generates a password hash using argon2.

    Args:
        plain_password: Plain text password

    Returns:
        str: Hashed password
    """
    return password_hasher.hash(plain_password)


def generate_otp_hash(plain_otp: str) -> str:
    """
    Generates an OTP hash using argon2.

    Args:
        plain_otp: Plain text OTP

    Returns:
        str: Hashed OTP
    """
    return password_hasher.hash(plain_otp)


def verify_password_hash(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain text password against a hashed password.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        bool: True if the password is correct, False otherwise
    """
    return password_hasher.verify(hashed_password, plain_password)


def verify_otp_hash(plain_otp: str, hashed_otp: str) -> bool:
    """
    Verifies a plain text OTP against a hashed OTP.

    Args:
        plain_otp: Plain text OTP
        hashed_otp: Hashed OTP

    Returns:
        bool: True if the OTP is correct, False otherwise
    """
    return password_hasher.verify(hashed_otp, plain_otp)


def create_access_token(subject: Union[str, Any], role: str, institution_id: str, expires_delta: timedelta = None) -> str:
    """
    Creates a JWT access token.

    Args:
        subject: User ID
        role: User role
        institution_id: Institution ID
        expires_delta: Expiration time delta

    Returns:
        str: JWT access token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject), "role": role, "institution_id": institution_id}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    """
    FastAPI dependency that validates the JWT Bearer token on every request.

    Raises HTTP 401 if the token is missing, expired, or has an invalid signature.
    Returns a typed TokenPayload containing sub (user_id), role, and institution_id.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=settings.JWT_ALGORITHM)
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        institution_id: str = payload.get("institution_id")
        if user_id is None or role is None:
            raise credentials_exception
        return TokenPayload(sub=user_id, role=role, institution_id=institution_id)
    except JWTError:
        raise credentials_exception


def require_role(*roles: str) -> Callable:
    """
    RBAC factory dependency.  Use as a route dependency:

        @router.get("/admin-only", dependencies=[Depends(require_role("admin"))])

    Or inject the token payload:

        @router.get("/admin-only")
        def route(current_user: TokenPayload = Depends(require_role("admin"))):
            ...

    Raises HTTP 403 if the authenticated user's role is not in the allowed list.
    """
    def checker(current_user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {', '.join(roles)}",
            )
        return current_user
    return checker
