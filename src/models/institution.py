from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class Institution(BaseModel):
  institution_id: UUID
  institution_name: str
  created_at: datetime
