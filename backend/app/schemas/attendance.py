from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class AttendanceSessionCreate(BaseModel):
    class_id: str
    subject_id: str
    date: str
    start_time: str = "09:00"


class AttendanceSessionResponse(BaseModel):
    id: str
    class_id: str
    subject_id: str
    teacher_id: str
    date: str
    start_time: str
    status: str
    created_at: Optional[datetime] = None


class AttendanceRecordCreate(BaseModel):
    student_id: str
    status: str


class AttendanceRecordBulk(BaseModel):
    records: List[AttendanceRecordCreate]


class AttendanceRecordUpdate(BaseModel):
    status: str


class AttendanceRecordResponse(BaseModel):
    id: str
    session_id: str
    student_id: str
    status: str
    marked_at: Optional[datetime] = None


class StudentAttendanceSummary(BaseModel):
    student_id: str
    total_classes: int
    present: int
    absent: int
    late: int
    excused: int
    attendance_percentage: float
