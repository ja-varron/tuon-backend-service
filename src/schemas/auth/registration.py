from pydantic import BaseModel, EmailStr, field_validator

class AdminSignupRequest(BaseModel):
    institution_name: str
    email: EmailStr
    password: str

    @field_validator('password')
    @classmethod
    def password_max_bytes(cls, v: str) -> str:
        """
        Enforce password length policy (max 72 characters for bcrypt).
        """
        if len(v.encode('utf-8')) > 72:
            raise ValueError("Password exceeds maximum length of 72 bytes.")
        return v

class AdminSignupResponse(BaseModel):
    message: str
    user_id: str
