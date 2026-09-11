from datetime import datetime
from typing import Optional
from bson import ObjectId
from app.database import get_database
from app.utils.helpers import serialize_id


async def get_dashboard_summary(teacher_id: str, limit: int = 6) -> dict:
    """Aggregated, teacher-scoped data for the dashboard control center.

    Every query is filtered by the authenticated teacher, so no one can see
    another user's students/classes/subjects/attendance. Safe defaults are
    returned when the account has no data yet.
    """
    db = get_database()
    today = datetime.now().strftime("%Y-%m-%d")
    month = datetime.now().strftime("%Y-%m")

    total_students = await db.students.count_documents(
        {"teacher_id": teacher_id, "is_active": True}
    )
    total_classes = await db.classes.count_documents({"teacher_id": teacher_id})
    total_subjects = await db.subjects.count_documents({"teacher_id": teacher_id})

    daily = await get_daily_report(teacher_id, date=today)
    monthly = await get_monthly_report(teacher_id, month=month)

    overall_pct = 0.0
    summaries = monthly.get("student_summaries") or []
    if summaries:
        overall_pct = (
            sum(s["attendance_percentage"] for s in summaries) / len(summaries)
        )

    class_name = {}
    async for cls in db.classes.find({"teacher_id": teacher_id}):
        class_name[str(cls["_id"])] = cls["name"]
    subject_name = {}
    async for subject in db.subjects.find({"teacher_id": teacher_id}):
        subject_name[str(subject["_id"])] = subject["name"]

    recent_sessions = []
    async for session in db.attendance_sessions.find(
        {"teacher_id": teacher_id}
    ).sort([("date", -1), ("start_time", -1)]).limit(limit):
        recent_sessions.append({
            "session_id": str(session["_id"]),
            "class_id": str(session["class_id"]),
            "class_name": class_name.get(str(session["class_id"]), "Unknown class"),
            "subject_id": str(session["subject_id"]),
            "subject_name": subject_name.get(str(session["subject_id"]), "Unknown subject"),
            "date": session["date"],
            "start_time": session.get("start_time") or "",
        })

    attention_students = []
    if summaries:
        student_names = {}
        async for student in db.students.find(
            {"teacher_id": teacher_id, "is_active": True},
            {"name": 1, "roll_number": 1},
        ):
            student_names[str(student["_id"])] = {
                "name": student["name"],
                "roll_number": student.get("roll_number") or "",
            }
        below = [
            s for s in summaries
            if s["attendance_percentage"] < 75.0 and str(s["student_id"]) in student_names
        ]
        below.sort(key=lambda s: s["attendance_percentage"])
        for s in below[:limit]:
            info = student_names[str(s["student_id"])]
            attention_students.append({
                "student_id": str(s["student_id"]),
                "name": info["name"],
                "roll_number": info["roll_number"],
                "attendance_percentage": s["attendance_percentage"],
            })

    attention_classes = []
    async for cls in db.classes.find({"teacher_id": teacher_id}):
        report = await get_class_report(teacher_id, str(cls["_id"]))
        if not report:
            continue
        rows = report.get("student_summaries") or []
        if not rows:
            continue
        avg = sum(s["attendance_percentage"] for s in rows) / len(rows)
        if avg < 75.0:
            attention_classes.append({
                "class_id": str(cls["_id"]),
                "name": cls["name"],
                "attendance_percentage": round(avg, 2),
            })
    attention_classes.sort(key=lambda c: c["attendance_percentage"])

    attention_subjects = []
    subject_ids = await db.attendance_sessions.distinct(
        "subject_id", {"teacher_id": teacher_id}
    )
    for sid in subject_ids:
        sessions_cursor = db.attendance_sessions.find(
            {"teacher_id": teacher_id, "subject_id": sid}, {"_id": 1}
        )
        session_ids = [str(s["_id"]) async for s in sessions_cursor]
        if not session_ids:
            continue
        present = await db.attendance_records.count_documents(
            {"session_id": {"$in": session_ids}, "teacher_id": teacher_id, "status": "present"}
        )
        total = await db.attendance_records.count_documents(
            {"session_id": {"$in": session_ids}, "teacher_id": teacher_id}
        )
        if total == 0:
            continue
        pct = (present / total) * 100
        if pct < 75.0:
            attention_subjects.append({
                "subject_id": sid,
                "name": subject_name.get(sid, "Unknown subject"),
                "attendance_percentage": round(pct, 2),
            })
    attention_subjects.sort(key=lambda s: s["attendance_percentage"])

    return {
        "totals": {
            "students": total_students,
            "classes": total_classes,
            "subjects": total_subjects,
        },
        "today": {
            "date": daily["date"],
            "present": daily["total_present"],
            "absent": daily["total_absent"],
            "late": daily["total_late"],
            "excused": daily["total_excused"],
            "records": daily["total_records"],
        },
        "overall_percentage": round(overall_pct, 2),
        "recent_sessions": recent_sessions,
        "attention": {
            "students": attention_students,
            "classes": attention_classes,
            "subjects": attention_subjects,
        },
    }


async def get_daily_report(teacher_id: str, class_id: Optional[str] = None, date: Optional[str] = None) -> dict:
    db = get_database()
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    query = {"date": date, "teacher_id": teacher_id}
    if class_id:
        query["class_id"] = class_id

    sessions = []
    async for session in db.attendance_sessions.find(query):
        sessions.append(serialize_id(session))

    session_ids = [s["id"] for s in sessions]
    if not session_ids:
        return {
            "date": date,
            "sessions": [],
            "total_present": 0,
            "total_absent": 0,
            "total_late": 0,
            "total_excused": 0,
            "total_records": 0,
        }

    records = []
    async for record in db.attendance_records.find(
        {"session_id": {"$in": session_ids}, "teacher_id": teacher_id}
    ):
        records.append(serialize_id(record))

    total_present = sum(1 for r in records if r["status"] == "present")
    total_absent = sum(1 for r in records if r["status"] == "absent")
    total_late = sum(1 for r in records if r["status"] == "late")
    total_excused = sum(1 for r in records if r["status"] == "excused")

    return {
        "date": date,
        "sessions": sessions,
        "total_present": total_present,
        "total_absent": total_absent,
        "total_late": total_late,
        "total_excused": total_excused,
        "total_records": len(records),
    }


async def get_monthly_report(teacher_id: str, class_id: Optional[str] = None, month: Optional[str] = None) -> dict:
    db = get_database()
    if not month:
        month = datetime.now().strftime("%Y-%m")

    query = {"date": {"$regex": f"^{month}"}, "teacher_id": teacher_id}
    if class_id:
        query["class_id"] = class_id

    sessions = []
    async for session in db.attendance_sessions.find(query):
        sessions.append(serialize_id(session))

    session_ids = [s["id"] for s in sessions]
    if not session_ids:
        return {"month": month, "total_sessions": 0, "student_summaries": []}

    records = []
    async for record in db.attendance_records.find(
        {"session_id": {"$in": session_ids}, "teacher_id": teacher_id}
    ):
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


async def get_student_report(teacher_id: str, student_id: str) -> dict:
    db = get_database()
    try:
        student = await db.students.find_one(
            {"_id": ObjectId(student_id), "teacher_id": teacher_id}
        )
    except Exception:
        return None
    if not student:
        return None

    records = []
    async for record in db.attendance_records.find(
        {"student_id": student_id, "teacher_id": teacher_id}
    ):
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


async def get_class_report(teacher_id: str, class_id: str) -> dict:
    db = get_database()
    try:
        cls = await db.classes.find_one(
            {"_id": ObjectId(class_id), "teacher_id": teacher_id}
        )
    except Exception:
        return None
    if not cls:
        return None

    total_sessions = await db.attendance_sessions.count_documents(
        {"class_id": class_id, "teacher_id": teacher_id}
    )

    students = []
    async for student in db.students.find(
        {"class_id": class_id, "teacher_id": teacher_id, "is_active": True}
    ):
        students.append(serialize_id(student))

    student_summaries = []
    for student in students:
        summary = await get_student_summary(teacher_id, student["id"])
        summary["student_name"] = student["name"]
        summary["roll_number"] = student["roll_number"]
        student_summaries.append(summary)

    return {
        "class_id": class_id,
        "class_name": cls["name"],
        "total_sessions": total_sessions,
        "student_summaries": student_summaries,
    }


async def get_student_summary(teacher_id: str, student_id: str) -> dict:
    db = get_database()
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