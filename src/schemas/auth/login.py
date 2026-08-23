from typing import Optional
from pydantic import BaseModel, EmailStr

class SigninRequest(BaseModel):
    email: EmailStr
    password: str

class ProfileResponse(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str
    institution_id: str

class SigninResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    profile: ProfileResponse
