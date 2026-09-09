import pytest_asyncio
from mongomock_motor import AsyncMongoMockClient

import app.database as db_module
from app.database import get_database, create_indexes
from scripts.seed_demo_data import (
    ensure_demo_dataset,
    DEMO_TEACHER,
    DEMO_STUDENTS,
    demo_class_id,
)

DEMO_EMAIL = DEMO_TEACHER["email"]


@pytest_asyncio.fixture(autouse=True)
async def db_setup():
    client = AsyncMongoMockClient()
    db_module.set_database(client["attendance_db_test"])
    await create_indexes()
    yield
    client.close()


async def _demo_uid(db):
    user = await db.users.find_one({"email": DEMO_EMAIL})
    return str(user["_id"])


async def _register_teacher(db, email):
    from app.core.security import hash_password

    res = await db.users.insert_one(
        {
            "name": "Other Teacher",
            "email": email,
            "password_hash": hash_password("password123"),
            "role": "teacher",
            "is_active": True,
        }
    )
    return str(res.inserted_id)


async def test_demo_seed_creates_full_dataset(db_setup):
    db = get_database()
    summary = await ensure_demo_dataset(db)

    assert summary["class_count"] == 1
    assert summary["subject_count"] == 1
    assert summary["student_count"] == 58

    uid = await _demo_uid(db)
    assert summary["teacher_id"] == uid

    assert await db.classes.count_documents({"teacher_id": uid}) == 1
    assert await db.subjects.count_documents({"teacher_id": uid}) == 1
    assert await db.students.count_documents({"teacher_id": uid}) == 58

    demo_class = await db.classes.find_one({"teacher_id": uid})
    assert (await db.students.count_documents(
        {"teacher_id": uid, "class_id": demo_class_id(demo_class)}
    )) == 58

    subject = await db.subjects.find_one({"teacher_id": uid, "code": "DEMO101"})
    assert str(subject["class_id"]) == demo_class_id(demo_class)


async def test_demo_seed_is_idempotent(db_setup):
    db = get_database()
    await ensure_demo_dataset(db)
    before_users = await db.users.count_documents({})
    before_classes = await db.classes.count_documents({})
    before_students = await db.students.count_documents({})
    before_subjects = await db.subjects.count_documents({})

    summary = await ensure_demo_dataset(db)

    assert summary["student_count"] == 58
    assert await db.users.count_documents({}) == before_users
    assert await db.classes.count_documents({}) == before_classes
    assert await db.students.count_documents({}) == before_students
    assert await db.subjects.count_documents({}) == before_subjects


async def test_demo_seed_self_heals_misowned_data(db_setup):
    db = get_database()
    await ensure_demo_dataset(db)
    uid = await _demo_uid(db)
    other = await _register_teacher(db, "other@example.com")

    st = await db.students.find_one({"teacher_id": uid})
    await db.students.update_one({"_id": st["_id"]}, {"$set": {"teacher_id": other}})
    demo_class = await db.classes.find_one({"teacher_id": uid})
    await db.classes.update_one({"_id": demo_class["_id"]}, {"$set": {"teacher_id": other}})

    summary = await ensure_demo_dataset(db)

    assert summary["class_count"] == 1
    assert summary["student_count"] == 58
    assert await db.classes.count_documents({"teacher_id": uid}) == 1
    assert await db.students.count_documents({"teacher_id": uid}) == 58


async def test_demo_seed_does_not_touch_personal_data(db_setup):
    db = get_database()
    other = await _register_teacher(db, "personal@example.com")

    from app.services.class_service import create_class
    from app.services.student_service import create_student
    from app.services.subject_service import create_subject

    cls = await create_class(
        {"name": "Personal Class", "semester": 1, "section": "A", "academic_year": "2026-27"},
        teacher_id=other,
    )
    await create_student(
        {
            "roll_number": "PER100",
            "name": "Personal Student",
            "email": "personal.student@example.com",
            "class_id": cls["id"],
            "semester": 1,
            "section": "A",
        },
        teacher_id=other,
    )
    await create_subject(
        {"name": "Personal Subj", "code": "PER101", "class_id": cls["id"]}, teacher_id=other
    )

    await ensure_demo_dataset(db)

    uid = await _demo_uid(db)
    assert uid != other

    # Demo dataset created alongside, personal data unchanged
    assert await db.classes.count_documents({"teacher_id": uid}) == 1
    assert await db.subjects.count_documents({"teacher_id": uid}) == 1
    assert await db.students.count_documents({"teacher_id": uid}) == 58
    assert await db.classes.count_documents({"teacher_id": other}) == 1
    assert await db.subjects.count_documents({"teacher_id": other}) == 1
    assert await db.students.count_documents({"teacher_id": other}) == 1
    assert await db.students.count_documents(
        {"teacher_id": other, "email": {"$regex": "@demo.attendvortex.local$"}}
    ) == 0


async def test_demo_student_count_matches_seed_list(db_setup):
    assert len(DEMO_STUDENTS) == 58