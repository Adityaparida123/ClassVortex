import pytest
from bson import ObjectId
from app.database import get_database


async def _register_and_login(client, name, email, password):
    await client.post("/api/v1/auth/register", json={
        "name": name,
        "email": email,
        "password": password,
        "role": "teacher",
    })
    login = await client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password,
    })
    assert login.status_code == 200
    return login.json()["data"]["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


async def _create_class(client, headers, name):
    resp = await client.post("/api/v1/classes", json={
        "name": name,
        "semester": 1,
        "section": "A",
        "academic_year": "2026-27",
    }, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["id"]


async def _create_subject(client, headers, class_id, code, name):
    resp = await client.post("/api/v1/subjects", json={
        "name": name,
        "code": code,
        "class_id": class_id,
        "teacher_id": "ignored",
    }, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["id"]


async def _create_student(client, headers, class_id, roll, name):
    resp = await client.post("/api/v1/students", json={
        "roll_number": roll,
        "name": name,
        "class_id": class_id,
        "semester": 1,
        "section": "A",
    }, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["id"]


async def _create_session(client, headers, class_id, subject_id, date="2026-09-10"):
    resp = await client.post("/api/v1/attendance/sessions", json={
        "class_id": class_id,
        "subject_id": subject_id,
        "date": date,
        "start_time": "09:00",
    }, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["id"]


async def _owner(client, tag):
    token = await _register_and_login(client, f"Bulk {tag}", f"bulk_{tag}@example.com", "password123")
    headers = _headers(token)
    class_id = await _create_class(client, headers, f"Bulk Class {tag}")
    subject_id = await _create_subject(client, headers, class_id, f"BLK{tag}", f"Bulk Subject {tag}")
    return headers, class_id, subject_id


@pytest.mark.asyncio
async def test_bulk_marks_multiple_students_once(client):
    headers, class_id, subject_id = await _owner(client, "multi")
    s1 = await _create_student(client, headers, class_id, "B001", "Bulk One")
    s2 = await _create_student(client, headers, class_id, "B002", "Bulk Two")
    s3 = await _create_student(client, headers, class_id, "B003", "Bulk Three")
    session_id = await _create_session(client, headers, class_id, subject_id)

    resp = await client.post(
        f"/api/v1/attendance/sessions/{session_id}/bulk",
        json={"records": [
            {"student_id": s1, "status": "present"},
            {"student_id": s2, "status": "absent"},
            {"student_id": s3, "status": "late"},
        ]},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert len(data) == 3

    db = get_database()
    assert await db.attendance_records.count_documents({"session_id": session_id}) == 3
    statuses = {
        r["student_id"]: r["status"]
        async for r in db.attendance_records.find({"session_id": session_id})
    }
    assert statuses == {s1: "present", s2: "absent", s3: "late"}


@pytest.mark.asyncio
async def test_bulk_retry_is_idempotent(client):
    headers, class_id, subject_id = await _owner(client, "idem")
    s1 = await _create_student(client, headers, class_id, "B004", "Bulk Idem One")
    s2 = await _create_student(client, headers, class_id, "B005", "Bulk Idem Two")
    session_id = await _create_session(client, headers, class_id, subject_id)

    payload = {"records": [
        {"student_id": s1, "status": "present"},
        {"student_id": s2, "status": "present"},
    ]}
    for _ in range(3):
        resp = await client.post(
            f"/api/v1/attendance/sessions/{session_id}/bulk",
            json=payload,
            headers=headers,
        )
        assert resp.status_code == 200, resp.text

    db = get_database()
    assert await db.attendance_records.count_documents({"session_id": session_id}) == 2

    resp = await client.post(
        f"/api/v1/attendance/sessions/{session_id}/bulk",
        json={"records": [{"student_id": s1, "status": "late"}]},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert await db.attendance_records.count_documents({"session_id": session_id}) == 2
    record = await db.attendance_records.find_one({"session_id": session_id, "student_id": s1})
    assert record["status"] == "late"


@pytest.mark.asyncio
async def test_bulk_skips_students_owned_or_other_user(client):
    headers, class_id, subject_id = await _owner(client, "skip")
    s1 = await _create_student(client, headers, class_id, "B006", "Bulk Skip One")
    session_id = await _create_session(client, headers, class_id, subject_id)

    # A student belonging to another teacher's class.
    other_token = await _register_and_login(client, "Other", "bulk_other@example.com", "password123")
    other_headers = _headers(other_token)
    other_class = await _create_class(client, other_headers, "Other Class")
    other_subject = await _create_subject(client, other_headers, other_class, "BLKOTH", "Other Subject")
    other_student = await _create_student(client, other_headers, other_class, "B007", "Bulk Other Student")

    resp = await client.post(
        f"/api/v1/attendance/sessions/{session_id}/bulk",
        json={"records": [
            {"student_id": s1, "status": "present"},
            {"student_id": other_student, "status": "present"},
        ]},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert len(resp.json()["data"]) == 1

    db = get_database()
    assert await db.attendance_records.count_documents({"session_id": session_id}) == 1


@pytest.mark.asyncio
async def test_bulk_requires_owned_session(client):
    headers, _, _ = await _owner(client, "nosess")
    other_token = await _register_and_login(client, "Attacker2", "bulk_attacker@example.com", "password123")
    other_headers = _headers(other_token)
    other_class = await _create_class(client, other_headers, "Attacker Class")
    other_subject = await _create_subject(client, other_headers, other_class, "BLKATK", "Attacker Subject")
    other_session = await _create_session(client, other_headers, other_class, other_subject)

    resp = await client.post(
        f"/api/v1/attendance/sessions/{other_session}/bulk",
        json={"records": []},
        headers=headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_bulk_nonexistent_session_returns_404(client):
    headers, _, _ = await _owner(client, "noexist")
    resp = await client.post(
        "/api/v1/attendance/sessions/000000000000000000000000/bulk",
        json={"records": []},
        headers=headers,
    )
    assert resp.status_code == 404