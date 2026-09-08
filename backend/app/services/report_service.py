from datetime import datetime
from typing import Optional
from bson import ObjectId
from app.database import get_database
from app.utils.helpers import serialize_id


async def get_daily_report(class_id: Optional[str] = None, date: Optional[str] = None) -> dict:
    db = get_database()
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    query = {"date": date}
    if class_id:
        query["class_id"] = class_id

    sessions = []
    async for session in db.attendance_sessions.find(query):
        sessions.append(serialize_id(session))

    session_ids = [s["id"] for s in sessions]
    if not session_ids:
        return {"date": date, "sessions": [], "total_present": 0, "total_absent": 0}

    records = []
    async for record in db.attendance_records.find({"session_id": {"$in": session_ids}}):
        records.append(serialize_id(record))

    total_present = sum(1 for r in records if r["status"] == "present")
    total_absent = sum(1 for r in records if r["status"] == "absent")

    return {
        "date": date,
        "sessions": sessions,
        "total_present": total_present,
        "total_absent": total_absent,
        "total_records": len(records),
    }


async def get_monthly_report(class_id: Optional[str] = None, month: Optional[str] = None) -> dict:
    db = get_database()
    if not month:
        month = datetime.now().strftime("%Y-%m")

    query = {"date": {"$regex": f"^{month}"}}
    if class_id:
        query["class_id"] = class_id

    sessions = []
    async for session in db.attendance_sessions.find(query):
        sessions.append(serialize_id(session))

    session_ids = [s["id"] for s in sessions]
    if not session_ids:
        return {"month": month, "total_sessions": 0, "student_summaries": []}

    records = []
    async for record in db.attendance_records.find({"session_id": {"$in": session_ids}}):
        records.append(serialize_id(record))

    student_stats = {}
    for record in records:
        sid = record["student_id"]
        if sid not in student_stats:
            student_stats[sid] = {"present": 0, "absent": 0, "late": 0, "excused": 0}
        status = record["status"]
        if status in student_stats[sid]:
            student_stats[sid][status] += 1

    student_summaries = []
    for sid, stats in student_stats.items():
        total = sum(stats.values())
        percentage = (stats["present"] / total * 100) if total > 0 else 0.0
        student_summaries.append({
            "student_id": sid,
            "total_classes": total,
            "present": stats["present"],
            "absent": stats["absent"],
            "late": stats["late"],
            "excused": stats["excused"],
            "attendance_percentage": round(percentage, 2),
        })

    return {
        "month": month,
        "total_sessions": len(sessions),
        "student_summaries": student_summaries,
    }


async def get_student_report(student_id: str) -> dict:
    db = get_database()
    student = await db.students.find_one({"_id": ObjectId(student_id)})
    if not student:
        return None

    records = []
    async for record in db.attendance_records.find({"student_id": student_id}):
        records.append(serialize_id(record))

    total = len(records)
    present = sum(1 for r in records if r["status"] == "present")
    absent = sum(1 for r in records if r["status"] == "absent")
    late = sum(1 for r in records if r["status"] == "late")
    excused = sum(1 for r in records if r["status"] == "excused")
    percentage = (present / total * 100) if total > 0 else 0.0

    return {
        "student_id": student_id,
        "student_name": student["name"],
        "roll_number": student["roll_number"],
        "total_classes": total,
        "present": present,
        "absent": absent,
        "late": late,
        "excused": excused,
        "attendance_percentage": round(percentage, 2),
    }


async def get_class_report(class_id: str) -> dict:
    db = get_database()
    cls = await db.classes.find_one({"_id": ObjectId(class_id)})
    if not cls:
        return None

    total_sessions = await db.attendance_sessions.count_documents({"class_id": class_id})

    students = []
    async for student in db.students.find({"class_id": class_id, "is_active": True}):
        students.append(serialize_id(student))

    student_summaries = []
    for student in students:
        summary = await get_student_summary(student["id"])
        summary["student_name"] = student["name"]
        summary["roll_number"] = student["roll_number"]
        student_summaries.append(summary)

    return {
        "class_id": class_id,
        "class_name": cls["name"],
        "total_sessions": total_sessions,
        "student_summaries": student_summaries,
    }


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
