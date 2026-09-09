from datetime import datetime, timezone
from bson import ObjectId
from app.database import get_database
from app.utils.helpers import serialize_id


async def find_student_attendance(query_text: str, teacher_id: str) -> dict:
    db = get_database()
    if db is None:
        return None
    tokens = [t.strip().lower() for t in query_text.replace("'", " ").replace("?", " ").split() if len(t.strip()) > 1]
    async for student in db.students.find({"is_active": True, "teacher_id": teacher_id}):
        st_name = student.get("name", "").lower()
        st_roll = student.get("roll_number", "").lower()
        if any(token in st_name.split() or token == st_roll for token in tokens):
            sid = str(student["_id"])
            total = await db.attendance_records.count_documents({"student_id": sid, "teacher_id": teacher_id})
            present = await db.attendance_records.count_documents({"student_id": sid, "teacher_id": teacher_id, "status": "present"})
            late = await db.attendance_records.count_documents({"student_id": sid, "teacher_id": teacher_id, "status": "late"})
            absent = await db.attendance_records.count_documents({"student_id": sid, "teacher_id": teacher_id, "status": "absent"})
            excused = await db.attendance_records.count_documents({"student_id": sid, "teacher_id": teacher_id, "status": "excused"})
            pct = round((present / total * 100), 2) if total > 0 else 0.0
            return {
                "student": serialize_id(student),
                "total": total,
                "present": present,
                "late": late,
                "absent": absent,
                "excused": excused,
                "percentage": pct,
            }
    return None


async def get_student_attendance(student_id: str, teacher_id: str) -> list:
    db = get_database()
    if db is None:
        return []
    records = []
    async for record in db.attendance_records.find({"student_id": student_id, "teacher_id": teacher_id}):
        records.append(serialize_id(record))
    return records


async def get_class_attendance(class_id: str, teacher_id: str) -> list:
    db = get_database()
    if db is None:
        return []
    sessions = []
    async for session in db.attendance_sessions.find({"class_id": class_id, "teacher_id": teacher_id}):
        sessions.append(serialize_id(session))
    return sessions


async def get_absent_students(teacher_id: str) -> list:
    db = get_database()
    if db is None:
        return []
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    records = []
    async for sess in db.attendance_sessions.find({"date": today_str, "teacher_id": teacher_id}):
        sess_id = str(sess["_id"])
        async for record in db.attendance_records.find(
            {"session_id": sess_id, "teacher_id": teacher_id, "status": "absent"}
        ):
            rec_data = serialize_id(record)
            try:
                st = await db.students.find_one(
                    {"_id": ObjectId(record["student_id"]), "teacher_id": teacher_id}
                )
                if st:
                    rec_data["student_name"] = st.get("name")
                    rec_data["roll_number"] = st.get("roll_number")
            except Exception:
                pass
            records.append(rec_data)

    if not records:
        async for record in db.attendance_records.find(
            {"status": "absent", "teacher_id": teacher_id}
        ).sort("_id", -1).limit(20):
            rec_data = serialize_id(record)
            try:
                st = await db.students.find_one(
                    {"_id": ObjectId(record["student_id"]), "teacher_id": teacher_id}
                )
                if st:
                    rec_data["student_name"] = st.get("name")
                    rec_data["roll_number"] = st.get("roll_number")
            except Exception:
                pass
            records.append(rec_data)
    return records


async def get_low_attendance_students(threshold: float, teacher_id: str) -> list:
    db = get_database()
    if db is None:
        return []
    students = []
    async for student in db.students.find({"is_active": True, "teacher_id": teacher_id}):
        student_data = serialize_id(student)
        sid = student_data["id"]
        total = await db.attendance_records.count_documents({"student_id": sid, "teacher_id": teacher_id})
        if total == 0:
            continue
        present = await db.attendance_records.count_documents(
            {"student_id": sid, "teacher_id": teacher_id, "status": "present"}
        )
        percentage = (present / total * 100)
        if percentage < threshold:
            student_data["attendance_percentage"] = round(percentage, 2)
            student_data["total_sessions"] = total
            student_data["present_sessions"] = present
            students.append(student_data)
    return students


async def get_monthly_report(month: str, teacher_id: str) -> dict:
    if not month:
        month = datetime.now(timezone.utc).strftime("%Y-%m")

    db = get_database()
    if db is None:
        return {"month": month, "total_sessions": 0}
    sessions = []
    async for session in db.attendance_sessions.find(
        {"date": {"$regex": f"^{month}"}, "teacher_id": teacher_id}
    ):
        sessions.append(serialize_id(session))
    return {"month": month, "total_sessions": len(sessions)}


async def get_student_details(student_id: str, teacher_id: str) -> dict:
    db = get_database()
    if db is None:
        return None
    try:
        student = await db.students.find_one(
            {"_id": ObjectId(student_id), "teacher_id": teacher_id}
        )
    except Exception:
        return None
    return serialize_id(student) if student else None