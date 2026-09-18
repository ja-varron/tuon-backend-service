from typing import Literal
from pydantic import BaseModel, EmailStr, Field

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    first_name: str
    middle_name: str | None = None
    last_name: str
    role: Literal['student', 'instructor']