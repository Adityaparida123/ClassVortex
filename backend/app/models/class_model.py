from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel


class ClassModel(BaseModel):
    id: Optional[str] = None
    teacher_id: str
    name: str
    semester: int
    section: str = "A"
    academic_year: str = "2026-27"
    is_active: bool = True
    created_at: datetime = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
