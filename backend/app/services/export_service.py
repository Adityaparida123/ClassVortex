import csv
import os
from datetime import datetime
from bson import ObjectId
from openpyxl import Workbook
from app.database import get_database
from app.config import settings
from app.utils.helpers import serialize_id

EXPORT_HEADERS = ["Date", "Class", "Subject", "Roll Number", "Student Name", "Status", "Teacher"]


def build_session_query(teacher_id: str, class_id: str = None, from_date: str = None, to_date: str = None) -> dict:
    query = {"teacher_id": teacher_id}
    if class_id:
        query["class_id"] = class_id
    if from_date and to_date:
        query["date"] = {"$gte": from_date, "$lte": to_date}
    elif from_date:
        query["date"] = {"$gte": from_date}
    elif to_date:
        query["date"] = {"$lte": to_date}
    return query


async def resolve_lookup(collection, raw_id):
    if not raw_id:
        return None
    try:
        return await collection.find_one({"_id": ObjectId(raw_id)})
    except Exception:
        return None


async def build_export_rows(teacher_id: str, class_id: str = None, from_date: str = None, to_date: str = None) -> list:
    db = get_database()
    query = build_session_query(teacher_id, class_id, from_date, to_date)

    sessions = []
    async for session in db.attendance_sessions.find(query).sort("date", -1):
        sessions.append(serialize_id(session))

    session_ids = [s["id"] for s in sessions]
    if not session_ids:
        return []

    records = []
    async for record in db.attendance_records.find({
        "session_id": {"$in": session_ids},
        "teacher_id": teacher_id,
    }):
        records.append(serialize_id(record))

    session_map = {s["id"]: s for s in sessions}
    rows = []
    for record in records:
        session = session_map.get(record["session_id"], {})

        cls = await resolve_lookup(db.classes, session.get("class_id"))
        subject = await resolve_lookup(db.subjects, session.get("subject_id"))
        student = await resolve_lookup(db.students, record.get("student_id"))
        teacher = await resolve_lookup(db.users, session.get("teacher_id"))

        rows.append({
            "Date": session.get("date", ""),
            "Class": cls["name"] if cls else session.get("class_id", ""),
            "Subject": subject["name"] if subject else session.get("subject_id", ""),
            "Roll Number": student["roll_number"] if student else "",
            "Student Name": student["name"] if student else "",
            "Status": record["status"],
            "Teacher": teacher["name"] if teacher else "",
        })

    return rows


async def export_attendance_csv(
    teacher_id: str, class_id: str = None, from_date: str = None, to_date: str = None
) -> str:
    rows = await build_export_rows(teacher_id, class_id, from_date, to_date)
    if not rows:
        return None

    os.makedirs(settings.EXPORT_DIRECTORY, exist_ok=True)
    filename = f"attendance_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = os.path.join(settings.EXPORT_DIRECTORY, filename)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=EXPORT_HEADERS)
        writer.writeheader()
        writer.writerows(rows)

    return filepath


async def export_attendance_excel(
    teacher_id: str, class_id: str = None, from_date: str = None, to_date: str = None
) -> str:
    rows = await build_export_rows(teacher_id, class_id, from_date, to_date)
    if not rows:
        return None

    os.makedirs(settings.EXPORT_DIRECTORY, exist_ok=True)
    filename = f"attendance_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join(settings.EXPORT_DIRECTORY, filename)

    wb = Workbook()
    ws = wb.active
    ws.title = "Attendance"
    ws.append(EXPORT_HEADERS)
    for row in rows:
        ws.append([row[header] for header in EXPORT_HEADERS])
    wb.save(filepath)

    return filepath