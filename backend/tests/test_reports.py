import pytest
from app.services import report_service, attendance_service, student_service, class_service, subject_service


@pytest.mark.asyncio
async def test_reports_flow():
    cls = await class_service.create_class({
        "name": "Report Test Class",
        "semester": 2,
        "section": "B",
    }, teacher_id="teacher")
    subject = await subject_service.create_subject({
        "name": "Report Subject",
        "code": "REPORTSUB",
        "class_id": cls["id"],
    }, teacher_id="teacher")
    student = await student_service.create_student({
        "roll_number": "REP001",
        "name": "Report Student",
        "class_id": cls["id"],
        "semester": 2,
    }, teacher_id="teacher")

    session = await attendance_service.create_session(
        {"class_id": cls["id"], "subject_id": subject["id"], "date": "2026-03-15", "start_time": "10:00"},
        teacher_id="teacher",
    )
    await attendance_service.bulk_create_records(session["id"], [
        {"student_id": student["id"], "status": "present"}
    ], teacher_id="teacher")

    daily = await report_service.get_daily_report("teacher", class_id=cls["id"], date="2026-03-15")
    assert daily["date"] == "2026-03-15"

    monthly = await report_service.get_monthly_report("teacher", class_id=cls["id"], month="2026-03")
    assert monthly["month"] == "2026-03"

    student_report = await report_service.get_student_report("teacher", student["id"])
    assert student_report is not None
    assert student_report["roll_number"] == "REP001"

    class_report = await report_service.get_class_report("teacher", cls["id"])
    assert class_report is not None
    assert class_report["class_name"] == "Report Test Class"


@pytest.mark.asyncio
async def test_reports_are_user_scoped():
    cls_a = await class_service.create_class({
        "name": "Report Class A",
        "semester": 2,
        "section": "A",
    }, teacher_id="teacher_a")
    cls_b = await class_service.create_class({
        "name": "Report Class B",
        "semester": 2,
        "section": "B",
    }, teacher_id="teacher_b")
    subject = await subject_service.create_subject({
        "name": "Subject A",
        "code": "SCOP001",
        "class_id": cls_a["id"],
    }, teacher_id="teacher_a")
    student_a = await student_service.create_student({
        "roll_number": "REP010",
        "name": "Student A",
        "class_id": cls_a["id"],
        "semester": 2,
    }, teacher_id="teacher_a")

    session = await attendance_service.create_session(
        {"class_id": cls_a["id"], "subject_id": subject["id"], "date": "2026-03-15"},
        teacher_id="teacher_a",
    )
    await attendance_service.bulk_create_records(session["id"], [
        {"student_id": student_a["id"], "status": "present"}
    ], teacher_id="teacher_a")

    # teacher_b cannot see teacher_a's class report or student report
    assert await report_service.get_class_report("teacher_b", cls_a["id"]) is None
    assert await report_service.get_student_report("teacher_b", student_a["id"]) is None
    # own report visible
    assert await report_service.get_class_report("teacher_a", cls_a["id"]) is not None
    # daily report for other teacher's class is empty
    daily_b = await report_service.get_daily_report("teacher_b", class_id=cls_a["id"], date="2026-03-15")
    assert daily_b["sessions"] == []