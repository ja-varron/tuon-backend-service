from pydantic import BaseModel
from typing import Optional


class TokenPayload(BaseModel):
    sub: str  # user_id
    role: str
    institution_id: str
    exp: Optional[int] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
