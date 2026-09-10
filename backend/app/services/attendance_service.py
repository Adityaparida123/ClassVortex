from datetime import datetime, timezone
from typing import Optional, List
from bson import ObjectId
from pymongo import UpdateOne
from app.database import get_database
from app.utils.helpers import serialize_id


def _ids_match(a, b) -> bool:
    if a is None or b is None:
        return False
    return str(a) == str(b)


async def _get_owned_subject(subject_id: str, teacher_id: str) -> Optional[dict]:
    db = get_database()
    try:
        subject = await db.subjects.find_one(
            {"_id": ObjectId(subject_id), "teacher_id": teacher_id, "is_active": True}
        )
    except Exception:
        return None
    return subject


async def _get_owned_session(session_id: str, teacher_id: str) -> Optional[dict]:
    db = get_database()
    try:
        session = await db.attendance_sessions.find_one(
            {"_id": ObjectId(session_id), "teacher_id": teacher_id}
        )
    except Exception:
        return None
    return session


async def _get_owned_student(student_id: str, teacher_id: str) -> Optional[dict]:
    db = get_database()
    try:
        student = await db.students.find_one(
            {"_id": ObjectId(student_id), "teacher_id": teacher_id}
        )
    except Exception:
        return None
    return student


async def create_session(data: dict, teacher_id: str) -> dict:
    db = get_database()
    subject = await _get_owned_subject(data["subject_id"], teacher_id)
    if subject is None:
        raise ValueError("Subject not found or not owned by this user")

    subject_class_id = str(subject.get("class_id"))
    provided_class_id = str(data.get("class_id") or "")
    if provided_class_id and provided_class_id != subject_class_id:
        raise ValueError("class_id does not match the selected subject's class")

    session_data = {
        "class_id": subject_class_id,
        "subject_id": str(subject["_id"]),
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
    teacher_id: str,
    page: int = 1,
    limit: int = 20,
    class_id: Optional[str] = None,
    subject_id: Optional[str] = None,
    date: Optional[str] = None,
) -> tuple:
    db = get_database()
    query = {"teacher_id": teacher_id}
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


async def get_session_by_id(session_id: str, teacher_id: str) -> Optional[dict]:
    session = await _get_owned_session(session_id, teacher_id)
    return serialize_id(session) if session else None


async def delete_session(session_id: str, teacher_id: str) -> bool:
    """Delete a session and all of its records.

    Returns True on success. Returns False if the session does not exist.
    Raises PermissionError if the session exists but belongs to another user.
    """
    db = get_database()
    try:
        session = await db.attendance_sessions.find_one({"_id": ObjectId(session_id)})
    except Exception:
        return False
    if session is None:
        return False
    if not _ids_match(session.get("teacher_id"), teacher_id):
        raise PermissionError(
            "This attendance session does not belong to your account."
        )
    await db.attendance_records.delete_many(
        {"session_id": session_id, "teacher_id": teacher_id}
    )
    await db.attendance_sessions.delete_one({"_id": ObjectId(session_id)})
    return True


async def create_record(session_id: str, student_id: str, status: str, teacher_id: str) -> dict:
    db = get_database()
    session = await _get_owned_session(session_id, teacher_id)
    if session is None:
        raise ValueError("Session not found or not owned by this user")
    student = await _get_owned_student(student_id, teacher_id)
    if student is None:
        raise ValueError("Student not found or not owned by this user")
    if student.get("class_id") and not _ids_match(student.get("class_id"), session.get("class_id")):
        raise ValueError("Student does not belong to the session's class")

    existing = await db.attendance_records.find_one(
        {"session_id": session_id, "student_id": student_id, "teacher_id": teacher_id}
    )
    if existing:
        raise ValueError("Attendance already marked for this student in this session")

    record_data = {
        "session_id": session_id,
        "student_id": student_id,
        "teacher_id": teacher_id,
        "status": status,
        "marked_at": datetime.now(timezone.utc),
    }
    result = await db.attendance_records.insert_one(record_data)
    record_data["id"] = str(result.inserted_id)
    return serialize_id(record_data)


async def bulk_create_records(session_id: str, records: List[dict], teacher_id: str) -> list:
    db = get_database()
    session = await _get_owned_session(session_id, teacher_id)
    if session is None:
        raise ValueError("Session not found or not owned by this user")

    # Load the teacher's students for this class ONCE (avoids N+1 lookups).
    class_id = str(session.get("class_id")) if session.get("class_id") else None
    student_query = {"teacher_id": teacher_id}
    if class_id:
        student_query["class_id"] = class_id
    owned_ids = set()
    cursor = db.students.find(student_query, {"_id": 1})
    async for student in cursor:
        owned_ids.add(str(student["_id"]))

    if not records or not owned_ids:
        return []

    now = datetime.now(timezone.utc)
    ops = []
    for record in records:
        student_id = str(record.get("student_id") or "")
        if student_id not in owned_ids:
            continue
        ops.append(
            UpdateOne(
                {
                    "session_id": session_id,
                    "student_id": student_id,
                    "teacher_id": teacher_id,
                },
                {
                    "$set": {
                        "status": record.get("status", "present"),
                        "marked_at": now,
                    },
                },
                upsert=True,
            )
        )

    if ops:
        await db.attendance_records.bulk_write(ops, ordered=False)

    result = db.attendance_records.find(
        {"session_id": session_id, "teacher_id": teacher_id}
    )
    created = []
    async for record in result:
        created.append(serialize_id(record))
    return created


async def update_record(record_id: str, status: str, teacher_id: str) -> Optional[dict]:
    db = get_database()
    try:
        result = await db.attendance_records.find_one_and_update(
            {"_id": ObjectId(record_id), "teacher_id": teacher_id},
            {"$set": {"status": status, "marked_at": datetime.now(timezone.utc)}},
            return_document=True,
        )
    except Exception:
        return None
    return serialize_id(result) if result else None


async def get_records_by_session(session_id: str, teacher_id: str) -> list:
    db = get_database()
    session = await _get_owned_session(session_id, teacher_id)
    if session is None:
        return []
    cursor = db.attendance_records.find({"session_id": session_id, "teacher_id": teacher_id})
    records = []
    async for record in cursor:
        records.append(serialize_id(record))
    return records


async def get_records_by_student(student_id: str, teacher_id: str) -> list:
    db = get_database()
    student = await _get_owned_student(student_id, teacher_id)
    if student is None:
        return []
    cursor = db.attendance_records.find({"student_id": student_id, "teacher_id": teacher_id})
    records = []
    async for record in cursor:
        records.append(serialize_id(record))
    return records


async def get_records_by_class(class_id: str, teacher_id: str, date: Optional[str] = None) -> list:
    db = get_database()
    query = {"class_id": class_id, "teacher_id": teacher_id}
    if date:
        query["date"] = date
    sessions_cursor = db.attendance_sessions.find(query)

    session_ids = []
    async for session in sessions_cursor:
        session_ids.append(str(session["_id"]))

    if not session_ids:
        return []

    cursor = db.attendance_records.find({
        "session_id": {"$in": session_ids},
        "teacher_id": teacher_id,
    })
    records = []
    async for record in cursor:
        records.append(serialize_id(record))
    return records


async def get_student_summary(student_id: str, teacher_id: str) -> dict:
    db = get_database()
    student = await _get_owned_student(student_id, teacher_id)
    if student is None:
        return {
            "student_id": student_id,
            "total_classes": 0,
            "present": 0,
            "absent": 0,
            "late": 0,
            "excused": 0,
            "attendance_percentage": 0.0,
        }

    record_filter = {"student_id": student_id, "teacher_id": teacher_id}
    total = await db.attendance_records.count_documents(record_filter)
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
        {**record_filter, "status": "present"}
    )
    absent = await db.attendance_records.count_documents(
        {**record_filter, "status": "absent"}
    )
    late = await db.attendance_records.count_documents(
        {**record_filter, "status": "late"}
    )
    excused = await db.attendance_records.count_documents(
        {**record_filter, "status": "excused"}
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