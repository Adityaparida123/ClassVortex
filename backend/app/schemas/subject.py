from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SubjectCreate(BaseModel):
    name: str
    code: str
    class_id: str
    teacher_id: str


class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    class_id: Optional[str] = None
    teacher_id: Optional[str] = None
    is_active: Optional[bool] = None


class SubjectResponse(BaseModel):
    id: str
    name: str
    code: str
    class_id: str
    teacher_id: str
    is_active: bool
    created_at: Optional[datetime] = None
