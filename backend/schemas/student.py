from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional


class StudentCreate(BaseModel):
    student_id: str
    full_name: str
    email: EmailStr
    department: Optional[str] = None


class StudentResponse(BaseModel):
    id: int
    student_id: str
    full_name: str
    email: EmailStr
    department: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)