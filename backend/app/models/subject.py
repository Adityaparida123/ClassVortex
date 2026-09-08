from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel


class SubjectModel(BaseModel):
    id: Optional[str] = None
    name: str
    code: str
    class_id: str
    teacher_id: str
    is_active: bool = True
    created_at: datetime = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
