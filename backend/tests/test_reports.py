import pytest
from app.services import report_service, attendance_service, student_service, class_service


@pytest.mark.asyncio
async def test_reports_flow():
    cls = await class_service.create_class({
        "name": "Report Test Class",
        "semester": 2,
        "section": "B",
    })
    student = await student_service.create_student({
        "roll_number": "REP001",
        "name": "Report Student",
        "class_id": cls["id"],
        "semester": 2,
    })

    session = await attendance_service.create_session(
        {"class_id": cls["id"], "subject_id": "subj1", "date": "2026-03-15", "start_time": "10:00"},
        teacher_id="teacher",
    )
    await attendance_service.bulk_create_records(session["id"], [
        {"student_id": student["id"], "status": "present"}
    ])

    daily = await report_service.get_daily_report(class_id=cls["id"], date="2026-03-15")
    assert daily["date"] == "2026-03-15"

    monthly = await report_service.get_monthly_report(class_id=cls["id"], month="2026-03")
    assert monthly["month"] == "2026-03"

    student_report = await report_service.get_student_report(student["id"])
    assert student_report is not None
    assert student_report["roll_number"] == "REP001"

    class_report = await report_service.get_class_report(cls["id"])
    assert class_report is not None
    assert class_report["class_name"] == "Report Test Class"
