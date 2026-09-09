import pytest
from app.services import attendance_service, student_service, class_service, subject_service


@pytest.mark.asyncio
async def test_attendance_calculation():
    cls = await class_service.create_class({
        "name": "Calc Test Class",
        "semester": 1,
        "section": "A",
    }, teacher_id="teacher")
    subject = await subject_service.create_subject({
        "name": "Calc Subject",
        "code": "CALCSUB",
        "class_id": cls["id"],
    }, teacher_id="teacher")
    student = await student_service.create_student({
        "roll_number": "CAL001",
        "name": "Calc Student",
        "class_id": cls["id"],
        "semester": 1,
    }, teacher_id="teacher")

    session1 = await attendance_service.create_session(
        {"class_id": cls["id"], "subject_id": subject["id"], "date": "2026-01-01", "start_time": "09:00"},
        teacher_id="teacher",
    )
    session2 = await attendance_service.create_session(
        {"class_id": cls["id"], "subject_id": subject["id"], "date": "2026-01-02", "start_time": "09:00"},
        teacher_id="teacher",
    )

    await attendance_service.bulk_create_records(session1["id"], [
        {"student_id": student["id"], "status": "present"}
    ], teacher_id="teacher")
    await attendance_service.bulk_create_records(session2["id"], [
        {"student_id": student["id"], "status": "absent"}
    ], teacher_id="teacher")

    summary = await attendance_service.get_student_summary(student["id"], teacher_id="teacher")
    assert summary["total_classes"] == 2
    assert summary["present"] == 1
    assert summary["absent"] == 1
    assert summary["attendance_percentage"] == 50.0


@pytest.mark.asyncio
async def test_create_session_rejects_foreign_subject():
    cls = await class_service.create_class({
        "name": "Owned Class",
        "semester": 1,
        "section": "A",
    }, teacher_id="owner")
    subject = await subject_service.create_subject({
        "name": "Owned Subject",
        "code": "OWN001",
        "class_id": cls["id"],
    }, teacher_id="owner")

    from app.services.attendance_service import create_session
    from pytest import raises
    with raises(ValueError):
        await create_session(
            {"class_id": cls["id"], "subject_id": subject["id"], "date": "2026-01-01"},
            teacher_id="attacker",
        )


@pytest.mark.asyncio
async def test_create_session_rejects_class_mismatch():
    cls_a = await class_service.create_class({
        "name": "Class A",
        "semester": 1,
        "section": "A",
    }, teacher_id="teacher")
    cls_b = await class_service.create_class({
        "name": "Class B",
        "semester": 1,
        "section": "B",
    }, teacher_id="teacher")
    subject = await subject_service.create_subject({
        "name": "Subject A",
        "code": "SUBA001",
        "class_id": cls_a["id"],
    }, teacher_id="teacher")

    from app.services.attendance_service import create_session
    from pytest import raises
    with raises(ValueError):
        await create_session(
            {"class_id": cls_b["id"], "subject_id": subject["id"], "date": "2026-01-01"},
            teacher_id="teacher",
        )