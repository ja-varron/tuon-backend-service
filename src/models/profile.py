from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class Profile(BaseModel):
  user_id: UUID
  email: EmailStr = Field(..., max_length=50)
  first_name: str = Field(..., max_length=50)
  middle_name: Optional[str] = Field(None, max_length=20)
  last_name: str = Field(..., max_length=30)
  role: str
  created_at: datetime
  updated_at: datetime
  institution_id: UUID
  examinee_id_number: str = Field(default="N/A", max_length=15)
