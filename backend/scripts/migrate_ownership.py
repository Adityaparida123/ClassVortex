"""One-time ownership migration for AttendVortex.

Assigns every user-owned resource to its correct owner (teacher_id) and
normalizes referenced ids to strings so the new ownership enforcement
(compound unique roll + teacher scoping) works correctly.

Rules:
  - Students: owner by email domain. ``@demo.attendvortex.local`` -> demo teacher,
    everything else -> the personal teacher.
  - Classes: owner from the students assigned to that class; if none, the
    personal teacher (known existing personal classes).
  - Subjects: owner from their class's teacher (fallback: personal teacher).
  - Attendance sessions: owner from their class's teacher (fallback: the
    student-derived owner); normalize class_id/subject_id to strings.
  - Attendance records: owner from their session's teacher_id; normalize
    session_id/student_id to strings.
  - Keep existing records: nothing is ever deleted.

Also drops the old global unique ``roll_number_1`` index so personal and demo
data can both hold roll "24E116B40", then (re)creates the correct indexes.

Usage:
    cd backend
    python scripts/migrate_ownership.py
"""
import sys
import os

_backend_dir = os.path.dirname(os.path.abspath(__file__))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)
if os.path.dirname(_backend_dir) not in sys.path:
    sys.path.insert(0, os.path.dirname(_backend_dir))

import asyncio
from bson import ObjectId

from app.database import get_database, connect_to_mongo, close_mongo_connection, create_indexes
from app.services.auth_service import register_user

DEMO_EMAIL = "demo@attendvortex.local"
DEMO_NAME = "AttendVortex Demo Teacher"
DEMO_PASSWORD = "DemoAttendVortex2026!"
PERSONAL_DEFAULT_EMAIL = "adityaparidaomm@gmail.com"


def _as_str(value) -> str:
    if value is None:
        return ""
    return str(value)


async def main():
    print("=== AttendVortex Ownership Migration ===\n")
    await connect_to_mongo()
    db = get_database()

    try:
        # 1. Resolve owners
        demo_user = await db.users.find_one({"email": DEMO_EMAIL})
        if not demo_user:
            print("Demo teacher not found, creating it...")
            demo_user = await register_user(
                name=DEMO_NAME, email=DEMO_EMAIL, password=DEMO_PASSWORD, role="teacher"
            )
        demo_uid = str(demo_user.get("_id") or demo_user.get("id") or "")

        personal_user = await db.users.find_one({"email": PERSONAL_DEFAULT_EMAIL})
        personal_uid = str(personal_user.get("_id") or personal_user.get("id") or "")
        print(f"Demo teacher id:     {demo_uid}")
        print(f"Personal teacher id: {personal_uid}")
        if not personal_uid:
            raise RuntimeError(
                f"Could not resolve the personal teacher id (email {PERSONAL_DEFAULT_EMAIL} not found)."
            )

        # 2. Students: teacher_id by email domain, class_id to string
        student_by_owner = {"demo": 0, "personal": 0}
        async for student in db.students.find({}):
            email = (student.get("email") or "").lower()
            owner = demo_uid if email.endswith("@demo.attendvortex.local") else personal_uid
            updates = {
                "teacher_id": owner,
                "class_id": _as_str(student.get("class_id")),
            }
            await db.students.update_one({"_id": student["_id"]}, {"$set": updates})
            student_by_owner["demo" if owner == demo_uid else "personal"] += 1
        print(f"Students stamped:    demo={student_by_owner['demo']}, personal={student_by_owner['personal']}")

        # 3. Classes: teacher_id from their students (fallback personal), keep teacher_id consistent
        #    (classes have no class_id field)
        class_by_owner = {"demo": 0, "personal": 0}
        async for cls in db.classes.find({}):
            owner = personal_uid
            ref = await db.students.find_one({"class_id": _as_str(cls["_id"])})
            if ref:
                owner = ref.get("teacher_id") or personal_uid
            await db.classes.update_one({"_id": cls["_id"]}, {"$set": {"teacher_id": _as_str(owner)}})
            class_by_owner["demo" if _as_str(owner) == demo_uid else "personal"] += 1
        print(f"Classes stamped:     demo={class_by_owner['demo']}, personal={class_by_owner['personal']}")

        # 4. Subjects: teacher_id from class, class_id to string
        subject_count = 0
        async for subject in db.subjects.find({}):
            owner = personal_uid
            class_id = _as_str(subject.get("class_id"))
            if class_id:
                try:
                    cls = await db.classes.find_one({"_id": ObjectId(class_id)})
                except Exception:
                    cls = None
                if cls:
                    owner = cls.get("teacher_id") or personal_uid
            updates = {"teacher_id": _as_str(owner), "class_id": class_id}
            await db.subjects.update_one({"_id": subject["_id"]}, {"$set": updates})
            subject_count += 1
        print(f"Subjects stamped:    {subject_count}")

        # 5. Sessions: teacher_id from class, ids to string
        session_count = 0
        session_teacher = {}
        async for session in db.attendance_sessions.find({}):
            owner = personal_uid
            class_id = _as_str(session.get("class_id"))
            if class_id:
                try:
                    cls = await db.classes.find_one({"_id": ObjectId(class_id)})
                except Exception:
                    cls = None
                if cls:
                    owner = cls.get("teacher_id") or personal_uid
            updates = {
                "teacher_id": _as_str(owner),
                "class_id": class_id,
                "subject_id": _as_str(session.get("subject_id")),
            }
            await db.attendance_sessions.update_one({"_id": session["_id"]}, {"$set": updates})
            session_teacher[_as_str(session["_id"])] = _as_str(owner)
            session_count += 1
        print(f"Sessions stamped:    {session_count}")

        # 6. Records: teacher_id from their session, ids to string
        record_count = 0
        async for record in db.attendance_records.find({}):
            session_id = _as_str(record.get("session_id"))
            owner = session_teacher.get(session_id) or personal_uid
            updates = {
                "teacher_id": _as_str(owner),
                "session_id": session_id,
                "student_id": _as_str(record.get("student_id")),
            }
            await db.attendance_records.update_one({"_id": record["_id"]}, {"$set": updates})
            record_count += 1
        print(f"Records stamped:     {record_count}")

        # 7. Drop the old global unique roll_number index, then (re)create correct indexes
        indexes = await db.students.index_information()
        for name in list(indexes.keys()):
            keys = indexes[name].get("key", [])
            if keys == [("roll_number", 1)] and indexes[name].get("unique"):
                await db.students.drop_index(name)
                print(f"Dropped legacy unique index: {name}")
                break
        await create_indexes()
        print("MongoDB indexes verified/created.")

        print("\n=== Migration complete ===")
    finally:
        await close_mongo_connection()
        print("MongoDB connection closed")


if __name__ == "__main__":
    asyncio.run(main())