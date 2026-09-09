"""Demo data seed script for AttendVortex (self-healing + idempotent).

Guarantees the demo account owns a complete, correctly-owned demo dataset:

  - demo teacher account (created if missing)
  - at least 1 demo class owned by the demo teacher
  - the DEMO101 subject owned by the demo teacher and attached to the demo class
  - all 58 demo students owned by the demo teacher and attached to the demo class
  - deterministic attendance sessions + records for the demo class/subject

Unlike the legacy script this is *self-healing*: every run re-verifies ownership
and repairs any demo-domain records that were created under the wrong user or
class. Non-demo (personal) data is NEVER touched, and existing demo data is
NEVER duplicated (the script is idempotent).

Usage:
    cd backend
    python scripts/seed_demo_data.py
"""
import sys
import os

# Ensure the parent directory (backend) is on the path so `from app.database import ...` works
_backend_dir = os.path.dirname(os.path.abspath(__file__))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)
if os.path.dirname(_backend_dir) not in sys.path:
    sys.path.insert(0, os.path.dirname(_backend_dir))

import asyncio
from datetime import datetime, timezone, timedelta

from app.database import get_database, connect_to_mongo, close_mongo_connection
from app.core.security import hash_password
from app.services.student_service import create_student
from app.services.class_service import create_class
from app.services.subject_service import create_subject
from app.services.attendance_service import (
    create_session,
    bulk_create_records,
    get_student_summary,
)


# ----- Demo data -----

DEMO_TEACHER = {
    "name": "AttendVortex Demo Teacher",
    "email": "demo@attendvortex.local",
    "password": "DemoAttendVortex2026!",
    "role": "teacher",
}

DEMO_CLASS = {
    "name": "CSE Demo Class",
    "semester": 3,
    "section": "A",
    "academic_year": "2026",
}

DEMO_SUBJECT = {
    "name": "Demo Attendance",
    "code": "DEMO101",
}

DEMO_STUDENTS = [
    (1, "2341019525", "SAGAR SINGH"),
    (2, "24E100A09", "YASHESWANI"),
    (3, "24E101A34", "MD OWAISH ALAM"),
    (4, "24E101A67", "ADITYA ARYAN"),
    (5, "24E102A11", "SHRADHA SUMAN BALIARSINGH"),
    (6, "24E102A27", "STHITA PRAGYAN BARIK"),
    (7, "24E102B95", "MANASMITA BRAHMA"),
    (8, "24E103A19", "INDRANEEL CHAUDHURI"),
    (9, "24E103A44", "SOAM SANKET CHOUDHURY"),
    (10, "24E104A33", "KUMARI BAISHNABI DAS"),
    (11, "24E104A36", "ARPITA PRIYADARSHINI DAS"),
    (12, "24E104B98", "DINESH DAS"),
    (13, "24E106A03", "ZOYA FATMA"),
    (14, "24E107A10", "PRABIN KUMAR GARTIA"),
    (15, "24E107A58", "VINEET GULERIA"),
    (16, "24E107A71", "KANAK GUPTA"),
    (17, "24E110A15", "ANANYA JENA"),
    (18, "24E111B43", "B ROSHAN KUMAR"),
    (19, "24E111B65", "ROHAN KUMAR"),
    (20, "24E111B97", "SHUBHANGNI KUMARI"),
    (21, "24E111C07", "SHRISTI KUMARI"),
    (22, "24E111C60", "RICKY HERMAN OUAMBO KAMGA"),
    (23, "24E113B04", "ABHISEK MISHRA"),
    (24, "24E113B34", "SOHAN MISHRA"),
    (25, "24E113B48", "ATULYA MISHRA"),
    (26, "24E114A76", "ARABINDA NAYAK"),
    (27, "24E116A09", "KUNDANIKA PADHI"),
    (28, "24E116A12", "SNEHASIS PADHI"),
    (29, "24E116A70", "SOUMYA RANJAN PANDA"),
    (30, "24E116B40", "ADITYA PARIDA"),
    (31, "24E116B74", "SUBHRAJEET PATI"),
    (32, "24E116B97", "ADITYA PRASAD PATRA"),
    (33, "24E116C07", "DHRUTI KISHORE PATRA"),
    (34, "24E116C51", "NANSHI PATTNAIK"),
    (35, "24E116D68", "SUSHOBHAN PRATIHARI"),
    (36, "24E116D91", "SASWATI PRIYADARSINI"),
    (37, "24E116E24", "ROUNAK PRASAD"),
    (38, "24E118A15", "KAUSHAL RAJ GUPTA"),
    (39, "24E118A32", "ANKIT RAJ"),
    (40, "24E119A64", "SWAGAT KUMAR SAHOO"),
    (41, "24E119A93", "PRITESH KUMAR SAHOO"),
    (42, "24E119B24", "SHANTANU KUMAR SAHOO"),
    (43, "24E119B77", "ESHWAR SAHU"),
    (44, "24E119B81", "PRATIK KUMAR SAHU"),
    (45, "24E119C05", "KARAN SINGH SAINI"),
    (46, "24E119C41", "ABHISHEK DYAN SAMANTARA"),
    (47, "24E119D07", "SOUMENDRA SETHY"),
    (48, "24E119D62", "ADITYA KUMAR SHYAM"),
    (49, "24E119D90", "HARSHA KUMAR SINGH"),
    (50, "24E119F30", "SAHIL SAHOO"),
    (51, "24E119F55", "SRIYA SAHOO"),
    (52, "24E119F58", "JYOTIRAJ SAHU"),
    (53, "24E119F72", "ARYAN PRATAP SINGH"),
    (54, "24E119F75", "BISWA SARATHI SUBUDHI"),
    (55, "24E119G28", "S SRIMAYEE SUBUDHI"),
    (56, "24E119G40", "SUSHREE DEBANSI SAHOO"),
    (57, "24E119G43", "PRACHI SINGH"),
    (58, "24E120A40", "PRIYANSHU TATWAMASI"),
]

# Derived emails: roll_number@demo.attendvortex.local
DEMO_STUDENT_EMAILS = [f"{roll}@demo.attendvortex.local" for _, roll, _ in DEMO_STUDENTS]

DEMO_EMAIL_DOMAIN = "@demo.attendvortex.local"


def _as_str(value) -> str:
    return "" if value is None else str(value)


def demo_class_id(demo_class) -> str:
    return _as_str(demo_class.get("_id") or demo_class.get("id") or "")


def _is_demo_domain(email) -> bool:
    return (email or "").lower().endswith(DEMO_EMAIL_DOMAIN)


# ----- Helpers -----


async def _resolve_demo_teacher(db) -> dict:
    """Get the demo teacher document by email. Creates it if missing."""
    existing = await db.users.find_one({"email": DEMO_TEACHER["email"]})
    if existing:
        return existing

    user_data = {
        "name": DEMO_TEACHER["name"],
        "email": DEMO_TEACHER["email"],
        "password_hash": hash_password(DEMO_TEACHER["password"]),
        "role": DEMO_TEACHER["role"],
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.users.insert_one(user_data)
    user_data["_id"] = result.inserted_id
    return user_data


async def _ensure_demo_class(db, demo_uid: str) -> dict:
    """Ensure a class owned by the demo teacher exists.

    Prefers an existing demo-owned class. Adopts a mis-owned class only if it is
    clearly the demo class (its students are ALL demo-domain students, or it has
    no students at all). Otherwise creates a fresh demo class.
    """
    demo_uid = _as_str(demo_uid)

    # 1. Existing demo-owned class -> keep
    existing = await db.classes.find_one(
        {"name": DEMO_CLASS["name"], "section": DEMO_CLASS["section"], "teacher_id": demo_uid}
    )
    if existing:
        return existing

    # 2. Candidate class (same name/section) that is not demo-owned -> adopt only if safe
    cursor = db.classes.find({"name": DEMO_CLASS["name"], "section": DEMO_CLASS["section"]})
    async for cand in cursor:
        if _as_str(cand.get("teacher_id")) == demo_uid:
            return cand
        class_students = (
            await db.students.find({"class_id": _as_str(cand["_id"])}).to_list(length=None)
        )
        if all(_is_demo_domain(s.get("email")) for s in class_students):
            await db.classes.update_one({"_id": cand["_id"]}, {"$set": {"teacher_id": demo_uid}})
            return cand

    # 3. Create new demo class
    cls = await create_class(
        {
            "name": DEMO_CLASS["name"],
            "semester": DEMO_CLASS["semester"],
            "section": DEMO_CLASS["section"],
            "academic_year": DEMO_CLASS["academic_year"],
        },
        teacher_id=demo_uid,
    )
    return cls


async def _ensure_demo_subject(db, demo_uid: str, demo_class_id) -> dict:
    """Ensure DEMO101 is owned by the demo teacher and attached to the demo class."""
    demo_uid = _as_str(demo_uid)
    demo_class_id = _as_str(demo_class_id)

    # 1. Existing subject for the demo teacher -> fix class if needed
    existing = await db.subjects.find_one({"code": DEMO_SUBJECT["code"], "teacher_id": demo_uid})
    if existing:
        if _as_str(existing.get("class_id")) != demo_class_id:
            await db.subjects.update_one(
                {"_id": existing["_id"]}, {"$set": {"class_id": demo_class_id}}
            )
        return existing

    # 2. Orphaned DEMO101 pointing at the demo class -> adopt
    orphan = await db.subjects.find_one({"code": DEMO_SUBJECT["code"], "class_id": demo_class_id})
    if orphan:
        await db.subjects.update_one({"_id": orphan["_id"]}, {"$set": {"teacher_id": demo_uid}})
        return orphan

    # 3. Create new
    subject = await create_subject(
        {
            "name": DEMO_SUBJECT["name"],
            "code": DEMO_SUBJECT["code"],
            "class_id": demo_class_id,
        },
        teacher_id=demo_uid,
    )
    return subject


async def _ensure_demo_students(db, demo_uid: str, demo_class_id) -> list:
    """Ensure all 58 demo students exist, owned by the demo teacher + demo class.

    Self-heals mis-owned demo students (e.g., created under the personal teacher
    before ownership existed). Duplicate demo records that would violate the
    (teacher_id, roll_number) unique index are cleaned up. Non-demo students are
    never touched.
    """
    demo_uid = _as_str(demo_uid)
    demo_class_id = _as_str(demo_class_id)
    owned_ids = []

    for idx, (_, roll_number, name) in enumerate(DEMO_STUDENTS):
        email = DEMO_STUDENT_EMAILS[idx]

        docs = []
        cursor = db.students.find({"roll_number": roll_number})
        async for doc in cursor:
            docs.append(doc)

        demo_docs = [d for d in docs if _is_demo_domain(d.get("email"))]

        # --- No demo record for this roll -> create it ---
        if not demo_docs:
            try:
                student = await create_student(
                    {
                        "roll_number": str(roll_number),
                        "name": name,
                        "email": email,
                        "class_id": demo_class_id,
                        "semester": DEMO_CLASS["semester"],
                        "section": DEMO_CLASS["section"],
                    },
                    teacher_id=demo_uid,
                )
                owned_ids.append(str(student["id"]))
            except ValueError:
                existing = await db.students.find_one(
                    {"teacher_id": demo_uid, "roll_number": str(roll_number)}
                )
                if existing:
                    await db.students.update_one(
                        {"_id": existing["_id"]}, {"$set": {"class_id": demo_class_id}}
                    )
                    owned_ids.append(str(existing["_id"]))
            continue

        # --- Prefer a copy already owned by the demo teacher, else first demo doc ---
        canonical = next(
            (d for d in demo_docs if _as_str(d.get("teacher_id")) == demo_uid), demo_docs[0]
        )
        curr_owner = _as_str(canonical.get("teacher_id"))

        if curr_owner != demo_uid:
            # Moving ownership may collide with an existing demo-owned copy of this roll
            existing_demo = await db.students.find_one(
                {"teacher_id": demo_uid, "roll_number": str(roll_number)}
            )
            if existing_demo:
                await db.students.delete_one({"_id": canonical["_id"]})
                canonical = existing_demo
            else:
                await db.students.update_one(
                    {"_id": canonical["_id"]}, {"$set": {"teacher_id": demo_uid}}
                )

        updates = {
            "class_id": demo_class_id,
            "semester": DEMO_CLASS["semester"],
            "section": DEMO_CLASS["section"],
        }
        if (canonical.get("email") or "").lower() != email.lower():
            updates["email"] = email
        await db.students.update_one({"_id": canonical["_id"]}, {"$set": updates})
        owned_ids.append(str(canonical["_id"]))

        # --- Remove leftover duplicate demo records for the same roll ---
        for dup in demo_docs:
            if str(dup.get("_id")) != str(canonical.get("_id")):
                await db.students.delete_one({"_id": dup["_id"]})

    return owned_ids


async def _repair_demo_session_ownership(db, demo_uid: str, demo_class_id, demo_subject_id) -> int:
    """Re-stamp any attendance sessions/records that reference demo entities but
    were created under the wrong owner. Returns number of sessions repaired."""
    demo_uid = _as_str(demo_uid)
    demo_class_id = _as_str(demo_class_id)
    demo_subject_id = _as_str(demo_subject_id)
    repaired = 0

    cursor = db.attendance_sessions.find(
        {
            "$or": [
                {"class_id": demo_class_id},
                {"subject_id": demo_subject_id},
            ]
        }
    )
    async for session in cursor:
        if _as_str(session.get("teacher_id")) != demo_uid:
            await db.attendance_sessions.update_one(
                {"_id": session["_id"]}, {"$set": {"teacher_id": demo_uid}}
            )
            repaired += 1
        # Re-stamp records of repaired/owned sessions
        await db.attendance_records.update_many(
            {"session_id": _as_str(session["_id"])}, {"$set": {"teacher_id": demo_uid}}
        )
    return repaired


async def _ensure_demo_attendance(db, demo_uid: str, demo_class, demo_subject) -> int:
    """Create deterministic attendance sessions + records for the demo class.

    Session dates are anchored to the demo class creation date so the seed is
    idempotent no matter when it is re-run. Returns the number of sessions.
    """
    demo_uid = _as_str(demo_uid)
    demo_class_str = demo_class_id(demo_class)
    demo_subject_id = _as_str(demo_subject.get("_id") or demo_subject.get("id") or "")

    await _repair_demo_session_ownership(db, demo_uid, demo_class_str, demo_subject_id)

    created_at = demo_class.get("created_at") or datetime.now(timezone.utc)
    if isinstance(created_at, datetime):
        base_date = created_at.date()
    else:
        base_date = datetime.now(timezone.utc).date()
    session_dates = [(base_date - timedelta(days=i)).isoformat() for i in range(7)]

    for s_idx, session_date in enumerate(session_dates):
        existing_session = await db.attendance_sessions.find_one(
            {
                "class_id": demo_class_str,
                "subject_id": demo_subject_id,
                "date": session_date,
                "teacher_id": demo_uid,
            }
        )
        if existing_session:
            continue

        session = await create_session(
            {"class_id": demo_class_str, "subject_id": demo_subject_id, "date": session_date},
            teacher_id=demo_uid,
        )

        records = []
        for stu_idx, (_, roll_number, name) in enumerate(DEMO_STUDENTS):
            student = await db.students.find_one(
                {"teacher_id": demo_uid, "roll_number": str(roll_number)}
            )
            if not student:
                continue
            status = "present" if (stu_idx + s_idx) % 7 != 0 else "absent"
            records.append(
                {"session_id": session["id"], "student_id": str(student["_id"]), "status": status}
            )
        await bulk_create_records(session["id"], records, teacher_id=demo_uid)

    return await db.attendance_sessions.count_documents({"teacher_id": demo_uid})


async def ensure_demo_dataset(db) -> dict:
    """Idempotent, self-healing seed. Returns a summary dict with counts."""
    demo_teacher = await _resolve_demo_teacher(db)
    demo_uid = _as_str(demo_teacher.get("_id") or demo_teacher.get("id") or "")

    demo_class = await _ensure_demo_class(db, demo_uid)
    demo_subject = await _ensure_demo_subject(db, demo_uid, demo_class_id(demo_class))

    students = await _ensure_demo_students(db, demo_uid, demo_class_id(demo_class))
    session_count = await _ensure_demo_attendance(db, demo_uid, demo_class, demo_subject)

    return {
        "teacher_id": demo_uid,
        "teacher_email": DEMO_TEACHER["email"],
        "class_id": demo_class_id(demo_class),
        "class_count": await db.classes.count_documents({"teacher_id": demo_uid}),
        "subject_id": _as_str(demo_subject.get("_id") or demo_subject.get("id") or ""),
        "subject_count": await db.subjects.count_documents({"teacher_id": demo_uid}),
        "student_count": len(students),
        "session_count": session_count,
    }


async def main():
    print("=== AttendVortex Demo Data Seed (self-healing) ===\n")

    await connect_to_mongo()
    db = get_database()

    try:
        summary = await ensure_demo_dataset(db)

        demo_uid = summary["teacher_id"]
        print(f"1. Demo teacher:      {summary['teacher_email']} (id {demo_uid})")
        print(f"2. Demo classes:      {summary['class_count']}   (class id {summary['class_id']})")
        print(f"3. Demo subjects:     {summary['subject_count']}   (subject id {summary['subject_id']})")
        print(f"4. Demo students:     {summary['student_count']}")
        print(f"5. Demo sessions:     {summary['session_count']}")

        print("\n6. Verifying attendance summaries (first 3 students):")
        for stu_idx in [0, 2, 5]:
            roll_number = DEMO_STUDENTS[stu_idx][1]
            name = DEMO_STUDENTS[stu_idx][2]
            s_doc = await db.students.find_one({"teacher_id": demo_uid, "roll_number": str(roll_number)})
            if s_doc:
                stat = await get_student_summary(str(s_doc["_id"]), demo_uid)
                print(
                    f"   {name} (roll {roll_number}): "
                    f"{stat['present']}present/{stat['total_classes']}sessions = "
                    f"{stat['attendance_percentage']}%"
                )

        print("\n=== Done ===")
    finally:
        await close_mongo_connection()
        print("MongoDB connection closed")


if __name__ == "__main__":
    asyncio.run(main())