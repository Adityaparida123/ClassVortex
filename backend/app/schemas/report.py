from pydantic import BaseModel
from typing import Optional, List


class DailyReportRequest(BaseModel):
    class_id: Optional[str] = None
    date: Optional[str] = None


class MonthlyReportRequest(BaseModel):
    class_id: Optional[str] = None
    month: Optional[str] = None


class StudentReportResponse(BaseModel):
    student_id: str
    student_name: str
    roll_number: str
    total_classes: int
    present: int
    absent: int
    late: int
    excused: int
    attendance_percentage: float


class ClassReportResponse(BaseModel):
    class_id: str
    class_name: str
    total_sessions: int
    student_summaries: List[StudentReportResponse]
