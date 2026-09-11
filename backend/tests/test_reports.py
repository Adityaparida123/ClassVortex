import pytest
from datetime import datetime
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


@pytest.mark.asyncio
async def test_daily_report_counts_late_and_excused():
    cls = await class_service.create_class({"name": "Daily Class", "semester": 1, "section": "A"}, teacher_id="teacher")
    subject = await subject_service.create_subject({"name": "Daily Subject", "code": "DSUB", "class_id": cls["id"]}, teacher_id="teacher")
    students = []
    for i, roll in enumerate(["D001", "D002", "D003", "D004"]):
        students.append(await student_service.create_student(
            {"roll_number": roll, "name": f"Daily {roll}", "class_id": cls["id"], "semester": 1},
            teacher_id="teacher",
        ))

    session = await attendance_service.create_session(
        {"class_id": cls["id"], "subject_id": subject["id"], "date": "2026-03-20", "start_time": "10:00"},
        teacher_id="teacher",
    )
    await attendance_service.bulk_create_records(session["id"], [
        {"student_id": students[0]["id"], "status": "present"},
        {"student_id": students[1]["id"], "status": "absent"},
        {"student_id": students[2]["id"], "status": "late"},
        {"student_id": students[3]["id"], "status": "excused"},
    ], teacher_id="teacher")

    daily = await report_service.get_daily_report("teacher", class_id=cls["id"], date="2026-03-20")
    assert daily["total_present"] == 1
    assert daily["total_absent"] == 1
    assert daily["total_late"] == 1
    assert daily["total_excused"] == 1
    assert daily["total_records"] == 4


@pytest.mark.asyncio
async def test_dashboard_summary_aggregates_and_is_scoped():
    cls = await class_service.create_class({"name": "Dash Class", "semester": 2, "section": "A"}, teacher_id="teacher")
    subject = await subject_service.create_subject({"name": "Dash Subject", "code": "DASHSUB", "class_id": cls["id"]}, teacher_id="teacher")
    student_a = await student_service.create_student(
        {"roll_number": "SA001", "name": "Student A", "class_id": cls["id"], "semester": 2},
        teacher_id="teacher",
    )
    student_b = await student_service.create_student(
        {"roll_number": "SB001", "name": "Student B", "class_id": cls["id"], "semester": 2},
        teacher_id="teacher",
    )

    today = datetime.now().strftime("%Y-%m-%d")
    session = await attendance_service.create_session(
        {"class_id": cls["id"], "subject_id": subject["id"], "date": today, "start_time": "09:00"},
        teacher_id="teacher",
    )
    await attendance_service.bulk_create_records(session["id"], [
        {"student_id": student_a["id"], "status": "present"},
        {"student_id": student_b["id"], "status": "absent"},
    ], teacher_id="teacher")

    summary = await report_service.get_dashboard_summary("teacher")

    assert summary["totals"]["students"] == 2
    assert summary["totals"]["classes"] == 1
    assert summary["totals"]["subjects"] == 1

    assert summary["today"]["present"] == 1
    assert summary["today"]["absent"] == 1
    assert summary["today"]["records"] == 2

    # recent session carries class/subject names
    assert len(summary["recent_sessions"]) >= 1
    assert summary["recent_sessions"][0]["class_name"] == "Dash Class"
    assert summary["recent_sessions"][0]["subject_name"] == "Dash Subject"

    # Student B at 0% must appear in needs-attention
    names = {s["student_id"]: s for s in summary["attention"]["students"]}
    assert student_b["id"] in names
    assert names[student_b["id"]]["attendance_percentage"] < 75.0
    # Student A at 100% must not appear
    assert student_a["id"] not in names

    # subject average is 50% -> low attendance
    assert any(
        s["subject_id"] == subject["id"] for s in summary["attention"]["subjects"]
    )

    # another teacher sees only their (empty) dashboard
    empty = await report_service.get_dashboard_summary("other_teacher")
    assert empty["totals"]["students"] == 0
    assert empty["today"]["records"] == 0
    assert empty["attention"]["students"] == []
    assert empty["recent_sessions"] == []