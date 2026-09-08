from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class StudentCreate(BaseModel):
    roll_number: str
    name: str
    email: Optional[str] = ""
    phone: Optional[str] = ""
    class_id: str
    semester: int
    section: str = "A"


class StudentUpdate(BaseModel):
    roll_number: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    class_id: Optional[str] = None
    semester: Optional[int] = None
    section: Optional[str] = None
    is_active: Optional[bool] = None


class StudentResponse(BaseModel):
    id: str
    roll_number: str
    name: str
    email: Optional[str] = ""
    phone: Optional[str] = ""
    class_id: str
    semester: int
    section: str
    is_active: bool
    created_at: Optional[datetime] = None
