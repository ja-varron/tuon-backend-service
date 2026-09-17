from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import UUID

class OTPFlow(BaseModel):
  otp_flow_id: UUID
  user_id: UUID
  email: EmailStr
  institution_name: str
  otp_hash: str
  attempts: int = 0
  is_active: bool = True
  expires_at: datetime
