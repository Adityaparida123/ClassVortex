import pytest
from app.services import attendance_service, student_service, class_service
from app.database import get_database


@pytest.mark.asyncio
async def test_attendance_calculation():
    db = get_database()
    cls = await class_service.create_class({
        "name": "Calc Test Class",
        "semester": 1,
        "section": "A",
    })
    student = await student_service.create_student({
        "roll_number": "CAL001",
        "name": "Calc Student",
        "class_id": cls["id"],
        "semester": 1,
    })

    session1 = await attendance_service.create_session(
        {"class_id": cls["id"], "subject_id": "subj1", "date": "2026-01-01", "start_time": "09:00"},
        teacher_id="teacher",
    )
    session2 = await attendance_service.create_session(
        {"class_id": cls["id"], "subject_id": "subj1", "date": "2026-01-02", "start_time": "09:00"},
        teacher_id="teacher",
    )

    await attendance_service.bulk_create_records(session1["id"], [
        {"student_id": student["id"], "status": "present"}
    ])
    await attendance_service.bulk_create_records(session2["id"], [
        {"student_id": student["id"], "status": "absent"}
    ])

    summary = await attendance_service.get_student_summary(student["id"])
    assert summary["total_classes"] == 2
    assert summary["present"] == 1
    assert summary["absent"] == 1
    assert summary["attendance_percentage"] == 50.0
