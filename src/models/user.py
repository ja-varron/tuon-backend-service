from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

class User(BaseModel):
  user_id: UUID
  email: EmailStr
  encrypted_password: str
  email_created_at: Optional[datetime] = None