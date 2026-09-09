import pytest
from app.services import student_service


@pytest.mark.asyncio
async def test_student_service_create_and_get():
    student = await student_service.create_student({
        "roll_number": "SRV001",
        "name": "Service Test Student",
        "class_id": "test_class",
        "semester": 3,
        "section": "A",
    }, teacher_id="teacher_a")
    assert student["roll_number"] == "SRV001"
    assert student["teacher_id"] == "teacher_a"

    fetched = await student_service.get_student_by_id(student["id"], "teacher_a")
    assert fetched is not None
    assert fetched["name"] == "Service Test Student"


@pytest.mark.asyncio
async def test_student_service_filter():
    await student_service.create_student({
        "roll_number": "SRV002",
        "name": "Filter Match Student",
        "class_id": "test_class",
        "semester": 3,
        "section": "A",
    }, teacher_id="teacher_a")

    students, total = await student_service.get_students("teacher_a", search="Filter Match")
    assert total >= 1
    assert all(s["teacher_id"] == "teacher_a" for s in students)

    filtered_class, class_total = await student_service.get_students("teacher_a", class_id="test_class")
    assert class_total >= 1


@pytest.mark.asyncio
async def test_student_service_ownership_enforced():
    created = await student_service.create_student({
        "roll_number": "SRV003",
        "name": "Owned Student",
        "class_id": "test_class",
        "semester": 3,
        "section": "A",
    }, teacher_id="teacher_a")

    own = await student_service.get_student_by_id(created["id"], "teacher_a")
    assert own is not None

    other = await student_service.get_student_by_id(created["id"], "teacher_b")
    assert other is None