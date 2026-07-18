from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime

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


class UserCreate(BaseModel):
  email: EmailStr
  name: str


class UserUpdate(BaseModel):
  name: str | None = None
  is_active: bool | None = None
  role: str | None = None


class UserResponse(BaseModel):
  """
  Response model for user.
  """
  user_id: UUID
  email: str
  name: str
  is_active: bool
  created_at: datetime
  updated_at: datetime

  model_config = {
    "from_attributes": True
  }
  