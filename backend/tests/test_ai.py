import pytest
from datetime import datetime, timezone

import app.ai.assistant_service as assistant_service


EMAIL_INDEX = {"n": 0}


def _next_email():
    EMAIL_INDEX["n"] += 1
    return f"ai_test_{EMAIL_INDEX['n']}_teacher@example.com"


PASSWORD = "aitestpass123"


async def _register_and_login(client, name, email, password, role="teacher"):
    await client.post(
        "/api/v1/auth/register",
        json={"name": name, "email": email, "password": password, "role": role},
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert login.status_code == 200
    return login.json()["data"]["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


async def _create_class(client, headers, name):
    resp = await client.post(
        "/api/v1/classes",
        json={"name": name, "semester": 1, "section": "A", "academic_year": "2026-27"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["id"]


async def _create_subject(client, headers, class_id, code, name):
    resp = await client.post(
        "/api/v1/subjects",
        json={"name": name, "code": code, "class_id": class_id, "teacher_id": "ignored"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["id"]


async def _create_student(client, headers, class_id, roll, name):
    resp = await client.post(
        "/api/v1/students",
        json={
            "roll_number": roll,
            "name": name,
            "class_id": class_id,
            "semester": 1,
            "section": "A",
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["id"]


async def _chat(client, headers, message):
    resp = await client.post(
        "/api/v1/ai/chat", json={"message": message}, headers=headers
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


@pytest.fixture(autouse=True)
def _patch_llm(monkeypatch):
    """Force deterministic answers: the fake LLM echoes the required user message."""

    async def fake_chat(messages):
        return f"Responding to: {messages[-2]['content']}"

    monkeypatch.setattr(assistant_service.llm_client, "chat", fake_chat)


async def _setup_teacher(client):
    """Create a teacher with CSE (2 students) and ECE (1 student) and real records."""
    token = await _register_and_login(client, "AI Test Teacher", _next_email(), PASSWORD)
    headers = _headers(token)

    cse = await _create_class(client, headers, "CSE")
    ece = await _create_class(client, headers, "ECE")
    sub_ds = await _create_subject(client, headers, cse, "CS301", "Data Structures")
    sub_os = await _create_subject(client, headers, cse, "CS401", "Operating Systems")
    sub_dbms = await _create_subject(client, headers, ece, "CS302", "Database Management Systems")

    s1 = await _create_student(client, headers, cse, "AI001", "Aditya Parida")
    s2 = await _create_student(client, headers, cse, "AI002", "Sagar Singh")
    s3 = await _create_student(client, headers, ece, "AI003", "Prabin Gartia")

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for subject_id, class_id, students in [
        (sub_ds, cse, [(s1, "present"), (s2, "present")]),
        (sub_os, cse, [(s1, "present"), (s2, "absent")]),
        (sub_dbms, ece, [(s3, "absent")]),
    ]:
        sess = await client.post(
            "/api/v1/attendance/sessions",
            json={"class_id": class_id, "subject_id": subject_id, "date": date_str},
            headers=headers,
        )
        assert sess.status_code == 200, sess.text
        session_id = sess.json()["data"]["id"]
        bulk = await client.post(
            f"/api/v1/attendance/sessions/{session_id}/bulk",
            json={"records": [{"student_id": sid, "status": st} for sid, st in students]},
            headers=headers,
        )
        assert bulk.status_code == 200, bulk.text

    return headers


@pytest.mark.asyncio
async def test_class_lowest_attendance_routes_to_class_comparison(client):
    headers = await _setup_teacher(client)
    data = await _chat(client, headers, "Which class has the lowest attendance?")
    assert data["tool_used"] == "get_class_attendance_comparison"
    assert data["data"] and isinstance(data["data"], list)
    # ECE (single absent record) should rank lowest
    assert data["data"][0]["class_name"] == "ECE"
    assert data["data"][0]["attendance_percentage"] == 0.0
    # CSE (three present, one absent across two sessions) -> 75%
    cse = next(c for c in data["data"] if c["class_name"] == "CSE")
    assert cse["attendance_percentage"] == 75.0


@pytest.mark.asyncio
async def test_subjects_and_classes_route_together(client):
    headers = await _setup_teacher(client)
    data = await _chat(client, headers, "tell me all the subjects and classes we have")
    assert data["tool_used"] == "get_classes_and_subjects"
    class_names = {c["name"] for c in data["data"]["classes"]}
    subject_names = {s["name"] for s in data["data"]["subjects"]}
    assert class_names == {"CSE", "ECE"}
    assert {"Data Structures", "Operating Systems", "Database Management Systems"} <= subject_names


@pytest.mark.asyncio
async def test_subject_lowest_attendance_routes_to_subject_comparison(client):
    headers = await _setup_teacher(client)
    data = await _chat(client, headers, "Which subject has the lowest attendance?")
    assert data["tool_used"] == "get_subject_attendance_comparison"
    assert data["data"][0]["subject_name"] == "Database Management Systems"
    assert data["data"][0]["attendance_percentage"] == 0.0


@pytest.mark.asyncio
async def test_student_lowest_attendance_routes_to_ranking(client):
    headers = await _setup_teacher(client)
    data = await _chat(client, headers, "Which student has the lowest attendance?")
    assert data["tool_used"] == "get_student_attendance_ranking"
    assert data["data"][0]["name"] == "Prabin Gartia"


@pytest.mark.asyncio
async def test_low_attendance_below_75_routes_to_threshold_tool(client):
    headers = await _setup_teacher(client)
    data = await _chat(client, headers, "Show students below 75% attendance.")
    assert data["tool_used"] == "get_low_attendance_students"
    # Sagar has 50%, Prabin has 0% -> both below 75
    names = {s["name"] for s in data["data"]}
    assert "Sagar Singh" in names
    assert "Prabin Gartia" in names
    assert "Aditya Parida" not in names


@pytest.mark.asyncio
async def test_count_classes_routes_to_class_list(client):
    headers = await _setup_teacher(client)
    data = await _chat(client, headers, "How many classes do I have?")
    assert data["tool_used"] == "get_all_classes"
    assert len(data["data"]) == 2


@pytest.mark.asyncio
async def test_count_subjects_routes_to_subject_list(client):
    headers = await _setup_teacher(client)
    data = await _chat(client, headers, "How many subjects do I have?")
    assert data["tool_used"] == "get_all_subjects"
    assert len(data["data"]) == 3


@pytest.mark.asyncio
async def test_count_students_total(client):
    headers = await _setup_teacher(client)
    data = await _chat(client, headers, "How many students are in my classes?")
    assert data["tool_used"] == "get_total_student_count"
    assert data["data"]["total_students"] == 3


@pytest.mark.asyncio
async def test_count_students_in_specific_class(client):
    headers = await _setup_teacher(client)
    data = await _chat(client, headers, "How many students are in CSE?")
    assert data["tool_used"] == "get_class_students"
    assert data["data"]["class_name"] == "CSE"
    assert data["data"]["student_count"] == 2


@pytest.mark.asyncio
async def test_today_attendance_routes(client):
    headers = await _setup_teacher(client)
    data = await _chat(client, headers, "Show me today's attendance.")
    assert data["tool_used"] == "get_today_attendance"
    assert data["data"]["total"] == 5


@pytest.mark.asyncio
async def test_student_name_query(client):
    headers = await _setup_teacher(client)
    data = await _chat(client, headers, "What is Aditya Parida's attendance?")
    assert data["tool_used"] == "find_student_attendance"
    assert data["data"]["student"]["name"] == "Aditya Parida"
    assert data["data"]["percentage"] == 100.0


@pytest.mark.asyncio
async def test_unrecognized_question_does_not_return_low_attendance(client):
    headers = await _setup_teacher(client)
    data = await _chat(client, headers, "Can you tell me what the weather is like?")
    assert data["tool_used"] is None
    assert "couldn't determine" in data["answer"]


@pytest.mark.asyncio
async def test_ai_isolation_between_teachers(client):
    headers = await _setup_teacher(client)

    other_token = await _register_and_login(client, "Other Teacher", _next_email(), PASSWORD)
    other_headers = _headers(other_token)
    await _create_class(client, other_headers, "MECH")

    data = await _chat(client, headers, "How many classes do I have?")
    assert len(data["data"]) == 2
    assert all(c["name"] != "MECH" for c in data["data"])

    other_data = await _chat(client, other_headers, "How many classes do I have?")
    assert len(other_data["data"]) == 1
    assert other_data["data"][0]["name"] == "MECH"


@pytest.mark.asyncio
async def test_ai_requires_auth(client):
    resp = await client.post("/api/v1/ai/chat", json={"message": "hi"})
    assert resp.status_code in (401, 403)