from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel


class AttendanceSessionModel(BaseModel):
    id: Optional[str] = None
    class_id: str
    subject_id: str
    teacher_id: str
    date: str
    start_time: str = "09:00"
    status: str = "completed"
    created_at: datetime = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


class AttendanceRecordModel(BaseModel):
    id: Optional[str] = None
    session_id: str
    student_id: str
    teacher_id: str
    status: str = "present"
    marked_at: datetime = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.marked_at is None:
            self.marked_at = datetime.now(timezone.utc)
