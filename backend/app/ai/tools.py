from bson import ObjectId
from app.database import get_database
from app.utils.helpers import serialize_id


async def get_student_attendance(student_id: str) -> list:
    db = get_database()
    records = []
    async for record in db.attendance_records.find({"student_id": student_id}):
        records.append(serialize_id(record))
    return records


async def get_class_attendance(class_id: str) -> list:
    db = get_database()
    sessions = []
    async for session in db.attendance_sessions.find({"class_id": class_id}):
        sessions.append(serialize_id(session))
    return sessions


async def get_absent_students() -> list:
    db = get_database()
    records = []
    async for record in db.attendance_records.find({"status": "absent"}):
        records.append(serialize_id(record))
    return records


async def get_low_attendance_students(threshold: float = 75.0) -> list:
    db = get_database()
    students = []
    async for student in db.students.find({"is_active": True}):
        student_data = serialize_id(student)
        sid = student_data["id"]
        total = await db.attendance_records.count_documents({"student_id": sid})
        if total == 0:
            continue
        present = await db.attendance_records.count_documents(
            {"student_id": sid, "status": "present"}
        )
        percentage = (present / total * 100)
        if percentage < threshold:
            student_data["attendance_percentage"] = round(percentage, 2)
            students.append(student_data)
    return students


async def get_monthly_report(month: str = None) -> dict:
    from datetime import datetime
    if not month:
        month = datetime.now().strftime("%Y-%m")

    db = get_database()
    sessions = []
    async for session in db.attendance_sessions.find({"date": {"$regex": f"^{month}"}}):
        sessions.append(serialize_id(session))
    return {"month": month, "total_sessions": len(sessions)}


async def get_student_details(student_id: str) -> dict:
    db = get_database()
    student = await db.students.find_one({"_id": ObjectId(student_id)})
    return serialize_id(student) if student else None
