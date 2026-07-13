# pyrefly: ignore [missing-import]
from pydantic import BaseModel, EmailStr

class SendOTPRequest(BaseModel):
  """
  Request model for sending OTP.
  """
  email: EmailStr


class VerifyOTPRequest(BaseModel):
  """
  Request model for verifying OTP.
  """
  flow_token: str
  otp_code: str


class Config:
  """
  Configuration for the Pydantic models.
  """
  str_strip_whitespace = True


class RefreshRequest(BaseModel):
  """
  Request model for refreshing the token.
  """
  refresh_token: str


class TokenResponse(BaseModel):
  """
  Response model for tokens.
  """
  access_token: str
  refresh_token: str | None = None
  token_type: str = "bearer"


class UserResponse(BaseModel):
  """
  Response model for user.
  """
  user_id: int
  email: str
  role: str
  