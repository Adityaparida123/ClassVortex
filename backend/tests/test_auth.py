import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_register_and_login(client):
    register_response = await client.post("/api/v1/auth/register", json={
        "name": "Test User",
        "email": "test@example.com",
        "password": "testpass123",
        "role": "admin",
    })

    if register_response.status_code == 200:
        assert register_response.json()["success"] is True
    elif register_response.status_code == 409:
        pass

    login_response = await client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "testpass123",
    })
    assert login_response.status_code == 200
    data = login_response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    return data["data"]["access_token"]


@pytest.mark.asyncio
async def test_protected_endpoint_without_token(client):
    response = await client.get("/api/v1/students")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_class_crud(client):
    token = await test_register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    create_response = await client.post("/api/v1/classes", json={
        "name": "B.Tech CSE",
        "semester": 3,
        "section": "A",
        "academic_year": "2026-27",
    }, headers=headers)
    assert create_response.status_code == 200
    class_id = create_response.json()["data"]["id"]

    list_response = await client.get("/api/v1/classes", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["success"] is True

    get_response = await client.get(f"/api/v1/classes/{class_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["data"]["name"] == "B.Tech CSE"

    delete_response = await client.delete(f"/api/v1/classes/{class_id}", headers=headers)
    assert delete_response.status_code == 200


@pytest.mark.asyncio
async def test_student_crud(client):
    token = await test_register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    class_resp = await client.post("/api/v1/classes", json={
        "name": "B.Tech CSE",
        "semester": 3,
        "section": "A",
    }, headers=headers)
    class_id = class_resp.json()["data"]["id"]

    create_response = await client.post("/api/v1/students", json={
        "roll_number": "CS001",
        "name": "Rahul Kumar",
        "email": "rahul@example.com",
        "class_id": class_id,
        "semester": 3,
        "section": "A",
    }, headers=headers)
    assert create_response.status_code == 200
    student_id = create_response.json()["data"]["id"]

    get_response = await client.get(f"/api/v1/students/{student_id}", headers=headers)
    assert get_response.status_code == 200

    await client.delete(f"/api/v1/students/{student_id}", headers=headers)
    await client.delete(f"/api/v1/classes/{class_id}", headers=headers)


@pytest.mark.asyncio
async def test_attendance_flow(client):
    token = await test_register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    class_resp = await client.post("/api/v1/classes", json={
        "name": "Test Class",
        "semester": 3,
        "section": "A",
    }, headers=headers)
    class_id = class_resp.json()["data"]["id"]

    student_resp = await client.post("/api/v1/students", json={
        "roll_number": "T001",
        "name": "Test Student",
        "class_id": class_id,
        "semester": 3,
    }, headers=headers)
    student_id = student_resp.json()["data"]["id"]

    session_resp = await client.post("/api/v1/attendance/sessions", json={
        "class_id": class_id,
        "subject_id": "test_subject_id",
        "date": "2026-09-08",
    }, headers=headers)
    assert session_resp.status_code == 200
    session_id = session_resp.json()["data"]["id"]

    bulk_resp = await client.post(f"/api/v1/attendance/sessions/{session_id}/bulk", json={
        "records": [
            {"student_id": student_id, "status": "present"}
        ]
    }, headers=headers)
    assert bulk_resp.status_code == 200

    summary_resp = await client.get(f"/api/v1/attendance/student/{student_id}/summary", headers=headers)
    assert summary_resp.status_code == 200
    summary = summary_resp.json()["data"]
    assert summary["present"] == 1

    await client.delete(f"/api/v1/students/{student_id}", headers=headers)
    await client.delete(f"/api/v1/classes/{class_id}", headers=headers)


@pytest.mark.asyncio
async def test_reports(client):
    token = await test_register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    daily_resp = await client.get("/api/v1/reports/daily", headers=headers)
    assert daily_resp.status_code == 200

    monthly_resp = await client.get("/api/v1/reports/monthly", headers=headers)
    assert monthly_resp.status_code == 200
