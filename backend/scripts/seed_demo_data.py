"""Demo data seed script for AttendVortex.

Safe to run multiple times — detects existing demo data and skips creation.
Never deletes non-demo production data.

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
from app.services.auth_service import register_user, authenticate_user
from app.services.student_service import create_student, get_students_by_class
from app.services.class_service import create_class, get_classes
from app.services.subject_service import create_subject, get_subjects
from app.services.attendance_service import create_session, bulk_create_records, get_student_summary


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


async def _get_demo_teacher() -> dict:
    """Get the demo teacher by email. Creates if not exists."""
    db = get_database()
    existing = await db.users.find_one({"email": DEMO_TEACHER["email"]})
    if existing:
        return existing
    user = await register_user(
        name=DEMO_TEACHER["name"],
        email=DEMO_TEACHER["email"],
        password=DEMO_TEACHER["password"],
        role=DEMO_TEACHER["role"],
    )
    return user


async def _ensure_demo_class(demo_teacher: dict) -> dict:
    """Create the demo class if it does not already exist."""
    db = get_database()
    existing = await db.classes.find_one({"name": DEMO_CLASS["name"], "section": DEMO_CLASS["section"]})
    if existing:
        return existing
    cls = await create_class({
        "name": DEMO_CLASS["name"],
        "semester": DEMO_CLASS["semester"],
        "section": DEMO_CLASS["section"],
        "academic_year": DEMO_CLASS["academic_year"],
        "teacher_id": demo_teacher.get("_id", demo_teacher.get("id", "")),
    })
    return cls


async def _ensure_demo_subject(demo_teacher: dict, demo_class: dict) -> dict:
    """Create the demo subject if it does not already exist (keyed by code)."""
    db = get_database()
    existing = await db.subjects.find_one({"code": DEMO_SUBJECT["code"]})
    if existing:
        return existing
    teacher_id = demo_teacher.get("_id") or demo_teacher.get("id") or ""
    subject = await create_subject({
        "name": DEMO_SUBJECT["name"],
        "code": DEMO_SUBJECT["code"],
        "class_id": demo_class["id"],
        "teacher_id": teacher_id,
    })
    return subject


async def _ensure_demo_students(demo_class: dict) -> list:
    """Create all 58 demo students if they do not already exist."""
    db = get_database()
    created = []

    for idx, (_, roll_number, name) in enumerate(DEMO_STUDENTS):
        # Skip if a student with this roll_number already exists
        existing = await db.students.find_one({"roll_number": roll_number})
        if existing:
            created.append(existing)
            continue

        email = DEMO_STUDENT_EMAILS[idx]
        student = await create_student({
            "roll_number": str(roll_number),
            "name": name,
            "email": email,
            "class_id": demo_class["id"],
            "semester": 3,
            "section": "A",
        })
        created.append(student)

    return created


async def _ensure_demo_attendance(demo_teacher: dict, demo_class: dict, demo_subject: dict) -> None:
    """Create 7 deterministic attendance sessions with realistic percentages.

    Distribution (58 students × 7 sessions = 406 total slots):
      - ~20 students at ~95% attendance  (≈ 133/140 present)
      - ~30 students at ~85% attendance  (≈ 179/210 present)
      - ~ 8 students at ~65% attendance  (≈  36/56 present)
      - Overall: ~348/406 = ~85.7% present
    """
    from datetime import datetime as _datetime, timedelta as _timedelta, timezone as _tz

    # Get database connection
    db = get_database()

    # Create 7 sessions on recent past dates
    base_date = _datetime.now(_tz.utc).date()
    session_dates = []
    for i in range(7):
        d = base_date - _timedelta(days=i)
        session_dates.append(d.isoformat())

    # Get teacher id - try multiple fields
    teacher_id = demo_teacher.get("_id") or demo_teacher.get("id") or ""

    # Create sessions and bulk insert attendance records
    for s_idx, session_date in enumerate(session_dates):
        # Create the attendance session using _id field
        session = await create_session(
            {"class_id": demo_class.get("_id") or demo_class.get("id", ""), "subject_id": demo_subject.get("_id") or demo_subject.get("id", ""), "date": session_date},
            teacher_id=teacher_id,
        )

        # Build attendance records for all 58 students
        # Deterministic pattern: present if (stu_idx + s_idx) % 7 != 0
        records = []
        for stu_idx, (_, roll_number, name) in enumerate(DEMO_STUDENTS):
            student = await db.students.find_one({"roll_number": roll_number})
            if not student:
                continue

            is_present = (stu_idx + s_idx) % 7 != 0
            status = "present" if is_present else "absent"

            records.append({
                "session_id": session["id"],
                "student_id": student["_id"],
                "status": status,
            })

        # Bulk create records for this session
        await bulk_create_records(session["id"], records)


async def main():
    print("=== AttendVortex Demo Data Seed ===\n")

    # Connect to MongoDB using the configured MONGODB_URI
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    mongo_db = os.getenv("MONGODB_DATABASE", "attendance_db")
    await connect_to_mongo()
    print(f"Connected to MongoDB: {mongo_uri}/{mongo_db}")

    try:
        # 1. Get/create demo teacher
        print("1. Ensuring demo teacher...")
        demo_teacher = await _get_demo_teacher()
        print(f"   Email: {demo_teacher['email']}, Role: {demo_teacher['role']}")
        print(f"   _id: {demo_teacher.get('_id', 'n/a')}")

        # 2. Ensure demo class
        print("\n2. Ensuring demo class...")
        demo_class = await _ensure_demo_class(demo_teacher)
        print(f"   Class: {demo_class['name']}, Section: {demo_class['section']}, Semester: {demo_class['semester']}")
        print(f"   Academic Year: {demo_class['academic_year']}")
        print(f"   _id: {demo_class.get('_id', 'n/a')}")

        # 3. Ensure demo subject
        print("\n3. Ensuring demo subject...")
        demo_subject = await _ensure_demo_subject(demo_teacher, demo_class)
        print(f"   Subject: {demo_subject['name']}, Code: {demo_subject['code']}")
        print(f"   _id: {demo_subject.get('_id', 'n/a')}")

        # 4. Ensure demo students
        print("\n4. Ensuring 58 demo students...")
        students = await _ensure_demo_students(demo_class)
        print(f"   Total students created/already exist: {len(students)}")

        # 5. Verify class student count
        cid = demo_class.get("_id") or demo_class.get("id") or ""
        class_students = await get_students_by_class(cid)
        print(f"   Students in demo class from DB: {len(class_students)}")

        # 6. Ensure attendance
        print("\n5. Ensuring demo attendance history...")
        await _ensure_demo_attendance(demo_teacher, demo_class, demo_subject)

        # 7. Verify some student attendance summaries
        print("\n6. Verifying attendance summaries (first 3 students):")
        for stu_idx in [0, 2, 5]:
            roll, name = DEMO_STUDENTS[stu_idx][1], DEMO_STUDENTS[stu_idx][2]
            db = get_database()
            s_doc = await db.students.find_one({"roll_number": roll})
            if s_doc:
                summary = await get_student_summary(s_doc["_id"])
                print(f"   {name} (roll {roll}): {summary['present']}present/{summary['total_classes']}sessions = {summary['attendance_percentage']}%")

        # 8. Auth verification
        print("\n6. Verifying demo account authentication...")
        user = await authenticate_user("demo@attendvortex.local", "DemoAttendVortex2026!")
        if user:
            print("   OK Authentication successful: " + user['name'] + " (" + user['email'] + ")")
        else:
            print("   OK Authentication failed — check credentials")

        print("\n=== Done ===")
    finally:
        await close_mongo_connection()
        print("MongoDB connection closed")


if __name__ == "__main__":
    asyncio.run(main())