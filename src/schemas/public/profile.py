from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class InstitutionInfo(BaseModel):
  institution_id: UUID
  institution_name: str


class ProfileMeResponse(BaseModel):
  user_id: UUID
  email: str
  first_name: str
  middle_name: Optional[str] = None
  last_name: str
  role: str
  examinee_id_number: str
  institution: InstitutionInfo
  created_at: datetime
  updated_at: datetime