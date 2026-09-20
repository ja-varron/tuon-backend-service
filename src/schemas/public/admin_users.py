from typing import Literal
from pydantic import BaseModel, EmailStr, Field, model_validator

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    first_name: str
    middle_name: str | None = None
    last_name: str
    role: Literal['student', 'instructor']
    # examinee_id_number: str | None = Field(default=None, max_length=6, description="Required if role is 'student'")

    # @model_validator(mode='after')
    # def validate_examinee_id_number(self):
    #     if self.role == 'student' and not self.examinee_id_number:
    #         raise ValueError("examinee_id_number is required for students")

    #     if  (self.role == 'instructor' or self.role == 'admin') and self.examinee_id_number:
    #         raise ValueError("examinee_id_number is only allowed for students")
    #     return self