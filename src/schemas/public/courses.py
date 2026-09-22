from pydantic import BaseModel, Field

class CreateCourseRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)