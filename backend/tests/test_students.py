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
    })
    assert student["roll_number"] == "SRV001"

    fetched = await student_service.get_student_by_id(student["id"])
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
    })

    students, total = await student_service.get_students(search="Filter Match")
    assert total >= 1

    filtered_class, class_total = await student_service.get_students(class_id="test_class")
    assert class_total >= 1
