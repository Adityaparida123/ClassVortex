from datetime import datetime, timezone
from typing import Optional, List
from bson import ObjectId
from app.database import get_database
from app.utils.helpers import serialize_id


async def create_session(data: dict, teacher_id: str) -> dict:
    db = get_database()
    session_data = {
        "class_id": data["class_id"],
        "subject_id": data["subject_id"],
        "teacher_id": teacher_id,
        "date": data["date"],
        "start_time": data.get("start_time", "09:00"),
        "status": "completed",
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.attendance_sessions.insert_one(session_data)
    session_data["id"] = str(result.inserted_id)
    return serialize_id(session_data)


async def get_sessions(
    page: int = 1,
    limit: int = 20,
    class_id: Optional[str] = None,
    subject_id: Optional[str] = None,
    date: Optional[str] = None,
) -> tuple:
    db = get_database()
    query = {}
    if class_id:
        query["class_id"] = class_id
    if subject_id:
        query["subject_id"] = subject_id
    if date:
        query["date"] = date

    skip = (page - 1) * limit
    cursor = db.attendance_sessions.find(query).sort("date", -1).skip(skip).limit(limit)
    sessions = []
    async for session in cursor:
        sessions.append(serialize_id(session))
    total = await db.attendance_sessions.count_documents(query)
    return sessions, total


async def get_session_by_id(session_id: str) -> Optional[dict]:
    db = get_database()
    session = await db.attendance_sessions.find_one({"_id": ObjectId(session_id)})
    return serialize_id(session) if session else None


async def create_record(session_id: str, student_id: str, status: str) -> dict:
    db = get_database()

    existing = await db.attendance_records.find_one(
        {"session_id": session_id, "student_id": student_id}
    )
    if existing:
        raise ValueError("Attendance already marked for this student in this session")

    record_data = {
        "session_id": session_id,
        "student_id": student_id,
        "status": status,
        "marked_at": datetime.now(timezone.utc),
    }
    result = await db.attendance_records.insert_one(record_data)
    record_data["id"] = str(result.inserted_id)
    return serialize_id(record_data)


async def bulk_create_records(session_id: str, records: List[dict]) -> list:
    db = get_database()
    created = []
    for record in records:
        try:
            result = await create_record(session_id, record["student_id"], record["status"])
            created.append(result)
        except ValueError:
            existing = await db.attendance_records.find_one(
                {"session_id": session_id, "student_id": record["student_id"]}
            )
            if existing:
                await db.attendance_records.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {"status": record["status"], "marked_at": datetime.now(timezone.utc)}},
                )
                created.append(serialize_id({**existing, "status": record["status"]}))
    return created


async def update_record(record_id: str, status: str) -> Optional[dict]:
    db = get_database()
    result = await db.attendance_records.find_one_and_update(
        {"_id": ObjectId(record_id)},
        {"$set": {"status": status, "marked_at": datetime.now(timezone.utc)}},
        return_document=True,
    )
    return serialize_id(result) if result else None


async def get_records_by_session(session_id: str) -> list:
    db = get_database()
    cursor = db.attendance_records.find({"session_id": session_id})
    records = []
    async for record in cursor:
        records.append(serialize_id(record))
    return records


async def get_records_by_student(student_id: str) -> list:
    db = get_database()
    cursor = db.attendance_records.find({"student_id": student_id})
    records = []
    async for record in cursor:
        records.append(serialize_id(record))
    return records


async def get_records_by_class(class_id: str, date: Optional[str] = None) -> list:
    db = get_database()
    sessions_cursor = db.attendance_sessions.find({"class_id": class_id})
    if date:
        sessions_cursor = db.attendance_sessions.find({"class_id": class_id, "date": date})

    session_ids = []
    async for session in sessions_cursor:
        session_ids.append(str(session["_id"]))

    if not session_ids:
        return []

    cursor = db.attendance_records.find({"session_id": {"$in": session_ids}})
    records = []
    async for record in cursor:
        records.append(serialize_id(record))
    return records


async def get_student_summary(student_id: str) -> dict:
    db = get_database()
    total = await db.attendance_records.count_documents({"student_id": student_id})
    if total == 0:
        return {
            "student_id": student_id,
            "total_classes": 0,
            "present": 0,
            "absent": 0,
            "late": 0,
            "excused": 0,
            "attendance_percentage": 0.0,
        }

    present = await db.attendance_records.count_documents(
        {"student_id": student_id, "status": "present"}
    )
    absent = await db.attendance_records.count_documents(
        {"student_id": student_id, "status": "absent"}
    )
    late = await db.attendance_records.count_documents(
        {"student_id": student_id, "status": "late"}
    )
    excused = await db.attendance_records.count_documents(
        {"student_id": student_id, "status": "excused"}
    )

    percentage = (present / total * 100) if total > 0 else 0.0

    return {
        "student_id": student_id,
        "total_classes": total,
        "present": present,
        "absent": absent,
        "late": late,
        "excused": excused,
        "attendance_percentage": round(percentage, 2),
    }
