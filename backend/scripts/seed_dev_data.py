import asyncio
from datetime import datetime, timezone, timedelta
import random
import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from app.core.security import hash_password


async def seed():
    print("Connecting to MongoDB...")
    client_kwargs = {
        "serverSelectionTimeoutMS": 10000,
        "connectTimeoutMS": 10000,
        "socketTimeoutMS": 45000,
    }
    if (
        settings.MONGODB_URI.startswith("mongodb+srv://")
        or "tls=true" in settings.MONGODB_URI.lower()
        or "ssl=true" in settings.MONGODB_URI.lower()
    ):
        client_kwargs["tlsCAFile"] = certifi.where()

    client = AsyncIOMotorClient(settings.MONGODB_URI, **client_kwargs)
    db = client[settings.MONGODB_DATABASE]

    # 1. Users
    print("Seeding users...")
    admin = await db.users.find_one({"email": "admin@example.com"})
    if not admin:
        admin_data = {
            "name": "Dr. Sarah Jenkins",
            "email": "admin@example.com",
            "password_hash": hash_password("admin123"),
            "role": "admin",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        res = await db.users.insert_one(admin_data)
        admin_id = str(res.inserted_id)
        print("  Created admin: admin@example.com / admin123")
    else:
        admin_id = str(admin["_id"])
        print("  Admin already exists: admin@example.com")

    teacher = await db.users.find_one({"email": "teacher@example.com"})
    if not teacher:
        teacher_data = {
            "name": "Prof. Alan Turing",
            "email": "teacher@example.com",
            "password_hash": hash_password("teacher123"),
            "role": "teacher",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        res = await db.users.insert_one(teacher_data)
        teacher_id = str(res.inserted_id)
        print("  Created teacher: teacher@example.com / teacher123")
    else:
        teacher_id = str(teacher["_id"])
        print("  Teacher already exists: teacher@example.com")

    # 2. Classes
    print("Seeding classes...")
    classes_spec = [
        {"name": "B.Tech Computer Science", "semester": 3, "section": "A", "academic_year": "2026-27"},
        {"name": "B.Tech Artificial Intelligence", "semester": 5, "section": "B", "academic_year": "2026-27"},
        {"name": "BCA Data Science", "semester": 1, "section": "A", "academic_year": "2026-27"},
    ]
    class_ids = []
    for spec in classes_spec:
        cls = await db.classes.find_one({"name": spec["name"], "semester": spec["semester"], "teacher_id": teacher_id})
        if not cls:
            doc = {**spec, "teacher_id": teacher_id, "is_active": True, "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)}
            res = await db.classes.insert_one(doc)
            class_ids.append(str(res.inserted_id))
            print(f"  Created class: {spec['name']}")
        else:
            class_ids.append(str(cls["_id"]))
            print(f"  Class exists: {spec['name']}")

    # 3. Subjects
    print("Seeding subjects...")
    subjects_spec = [
        {"name": "Data Structures & Algorithms", "code": "CS301", "class_index": 0},
        {"name": "Database Management Systems", "code": "CS302", "class_index": 0},
        {"name": "Neural Networks & Deep Learning", "code": "AI501", "class_index": 1},
        {"name": "Computer Vision", "code": "AI502", "class_index": 1},
        {"name": "Python for Data Science", "code": "DS101", "class_index": 2},
    ]
    subject_ids = []
    for s in subjects_spec:
        c_id = class_ids[s["class_index"]]
        sub = await db.subjects.find_one({"code": s["code"], "teacher_id": teacher_id})
        if not sub:
            doc = {
                "name": s["name"],
                "code": s["code"],
                "class_id": c_id,
                "teacher_id": teacher_id,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
            res = await db.subjects.insert_one(doc)
            subject_ids.append(str(res.inserted_id))
            print(f"  Created subject: {s['name']} ({s['code']})")
        else:
            subject_ids.append(str(sub["_id"]))
            print(f"  Subject exists: {s['name']}")

    # 4. Students
    print("Seeding students...")
    student_names = [
        ("Aarav Sharma", "CS01"),
        ("Ananya Iyer", "CS02"),
        ("Rohan Verma", "CS03"),
        ("Priya Patel", "CS04"),
        ("Kabir Mehta", "CS05"),
        ("Sneha Rao", "CS06"),
        ("Vikram Malhotra", "CS07"),
        ("Diya Nair", "CS08"),
        ("Ishaan Gupta", "CS09"),
        ("Tanvi Joshi", "CS10"),
        ("Arjun Reddy", "AI01"),
        ("Neha Sen", "AI02"),
        ("Aditya Roy", "AI03"),
        ("Meera Pillai", "AI04"),
        ("Varun Saxena", "AI05"),
    ]

    student_ids = []
    for i, (name, roll) in enumerate(student_names):
        c_id = class_ids[0] if i < 10 else class_ids[1]
        sem = 3 if i < 10 else 5
        sec = "A" if i < 10 else "B"
        st = await db.students.find_one({"roll_number": roll, "teacher_id": teacher_id})
        if not st:
            email = f"{name.lower().replace(' ', '.')}@example.com"
            doc = {
                "roll_number": roll,
                "name": name,
                "email": email,
                "class_id": c_id,
                "teacher_id": teacher_id,
                "semester": sem,
                "section": sec,
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
            res = await db.students.insert_one(doc)
            student_ids.append(str(res.inserted_id))
            print(f"  Created student: {name} ({roll})")
        else:
            student_ids.append(str(st["_id"]))

    # 5. Attendance Sessions & Records
    print("Seeding attendance sessions...")
    today = datetime.now(timezone.utc).date()
    dates = [today - timedelta(days=d) for d in range(5, -1, -1)]

    for d in dates:
        date_str = d.isoformat()
        existing_sess = await db.attendance_sessions.find_one({"date": date_str, "class_id": class_ids[0], "subject_id": subject_ids[0]})
        if not existing_sess:
            sess_doc = {
                "class_id": class_ids[0],
                "subject_id": subject_ids[0],
                "teacher_id": teacher_id,
                "date": date_str,
                "start_time": "09:00",
                "status": "completed",
                "created_at": datetime.now(timezone.utc),
            }
            res = await db.attendance_sessions.insert_one(sess_doc)
            sess_id = str(res.inserted_id)

            for st_id in student_ids[:10]:
                status = random.choices(["present", "absent", "late", "excused"], weights=[80, 10, 7, 3])[0]
                rec = {
                    "session_id": sess_id,
                    "student_id": st_id,
                    "teacher_id": teacher_id,
                    "status": status,
                    "marked_at": datetime.now(timezone.utc),
                }
                await db.attendance_records.insert_one(rec)
            print(f"  Created session + 10 records for {date_str} (Class: CS, Subject: DSA)")

    print("\nDatabase seeding completed successfully.")
    print("Sample login credentials:")
    print("  Admin:   admin@example.com   / admin123")
    print("  Teacher: teacher@example.com / teacher123")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
