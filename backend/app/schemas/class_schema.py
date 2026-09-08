from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ClassCreate(BaseModel):
    name: str
    semester: int
    section: str = "A"
    academic_year: str = "2026-27"


class ClassUpdate(BaseModel):
    name: Optional[str] = None
    semester: Optional[int] = None
    section: Optional[str] = None
    academic_year: Optional[str] = None
    is_active: Optional[bool] = None


class ClassResponse(BaseModel):
    id: str
    name: str
    semester: int
    section: str
    academic_year: str
    is_active: bool
    created_at: Optional[datetime] = None
