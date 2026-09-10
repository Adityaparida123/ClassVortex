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


async def _session_owner(client, email="a@example.com", password="password123"):
    token = await _register_and_login(client, "Tester A", email, password)
    headers = _headers(token)
    class_id = await _create_class(client, headers, "Delete Class A")
    subject_id = await _create_subject(client, headers, class_id, "DEL001", "Delete Subject A")
    return headers, class_id, subject_id


@pytest.mark.asyncio
async def test_owner_can_delete_own_session(client):
    headers, class_id, subject_id = await _session_owner(client, "owner_a@example.com")
    session_id = await _create_session(client, headers, class_id, subject_id)

    resp = await client.delete(f"/api/v1/attendance/sessions/{session_id}", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["message"] == "Attendance session deleted successfully."

    resp = await client.get(f"/api/v1/attendance/sessions/{session_id}", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_unauthenticated_cannot_delete_session(client):
    headers, class_id, subject_id = await _session_owner(client, "owner_b@example.com")
    session_id = await _create_session(client, headers, class_id, subject_id)

    resp = await client.delete(f"/api/v1/attendance/sessions/{session_id}")
    assert resp.status_code == 403  # HTTPBearer: no credentials

    resp = await client.delete(
        f"/api/v1/attendance/sessions/{session_id}",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert resp.status_code == 401

    resp = await client.get(f"/api/v1/attendance/sessions/{session_id}", headers=headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_user_cannot_delete_another_users_session(client):
    owner_headers, class_id, subject_id = await _session_owner(client, "owner_c@example.com")
    session_id = await _create_session(client, owner_headers, class_id, subject_id)

    attacker_token = await _register_and_login(client, "Attacker", "attacker_c@example.com", "password123")
    attacker_headers = _headers(attacker_token)

    resp = await client.delete(f"/api/v1/attendance/sessions/{session_id}", headers=attacker_headers)
    assert resp.status_code == 403
    assert "does not belong to your account" in resp.json()["detail"]

    resp = await client.get(f"/api/v1/attendance/sessions/{session_id}", headers=owner_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_delete_removes_attendance_records(client):
    headers, class_id, subject_id = await _session_owner(client, "owner_d@example.com")
    student_id = await _create_student(client, headers, class_id, "DEL002", "Delete Student D")
    session_id = await _create_session(client, headers, class_id, subject_id)

    resp = await client.post(
        f"/api/v1/attendance/sessions/{session_id}/bulk",
        json={"records": [{"student_id": student_id, "status": "present"}]},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text

    db = get_database()
    before = await db.attendance_records.count_documents({"session_id": session_id})
    assert before == 1

    resp = await client.delete(f"/api/v1/attendance/sessions/{session_id}", headers=headers)
    assert resp.status_code == 200

    after = await db.attendance_records.count_documents({"session_id": session_id})
    assert after == 0
    assert await db.attendance_sessions.count_documents({"_id": ObjectId(session_id)}) == 0


@pytest.mark.asyncio
async def test_delete_nonexistent_session_returns_404(client):
    headers, _, _ = await _session_owner(client, "owner_e@example.com")
    resp = await client.delete(
        "/api/v1/attendance/sessions/000000000000000000000000",
        headers=headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_repeated_delete_is_safe(client):
    headers, class_id, subject_id = await _session_owner(client, "owner_f@example.com")
    session_id = await _create_session(client, headers, class_id, subject_id)

    resp = await client.delete(f"/api/v1/attendance/sessions/{session_id}", headers=headers)
    assert resp.status_code == 200

    resp = await client.delete(f"/api/v1/attendance/sessions/{session_id}", headers=headers)
    assert resp.status_code == 404