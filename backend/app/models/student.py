from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel
from bson import ObjectId


class StudentModel(BaseModel):
    id: Optional[str] = None
    teacher_id: str
    roll_number: str
    name: str
    email: Optional[str] = ""
    phone: Optional[str] = ""
    class_id: str
    semester: int
    section: str = "A"
    is_active: bool = True
    created_at: datetime = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
