import pytest
import json
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


@pytest.mark.asyncio
async def test_export_excel_intent_dd_slash_mm_date(client):
    """'9/11/2026' style must parse as Indian DD/MM/YYYY.

    Today is %Y-%m-%d, so '11/09/2026' means 11 September 2026 (has data).
    If the date were mis-parsed as MM/DD it would become 2026-11-09 (no data).
    """
    headers = await _setup_teacher(client)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    day, month = today.split("-")[2], today.split("-")[1]
    data = await _chat(client, headers, f"Create the Excel sheet of attendance for {day}/{month}/2026")
    assert data["tool_used"] == "export_attendance"
    assert "Responding to" not in data["answer"]
    payload = data["data"]["export"]
    assert payload["format"] == "xlsx"
    assert payload["from_date"] == today
    assert payload["to_date"] == today
    assert payload["row_count"] == 5
    assert "Download" in data["answer"]


@pytest.mark.asyncio
async def test_export_csv_natural_language_date(client):
    headers = await _setup_teacher(client)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    day, month, year = today.split("-")[2], today.split("-")[1], today.split("-")[0]
    month_name = datetime(int(year), int(month), 1).strftime("%B")
    data = await _chat(client, headers, f"Export attendance for {int(day)} {month_name} {year} as CSV")
    assert data["tool_used"] == "export_attendance"
    payload = data["data"]["export"]
    assert payload["format"] == "csv"
    assert payload["from_date"] == today
    assert payload["row_count"] == 5


@pytest.mark.asyncio
async def test_export_intent_with_no_data_offers_no_download(client):
    headers = await _setup_teacher(client)
    data = await _chat(client, headers, "Export attendance for 1 January 2020")
    assert data["tool_used"] == "export_attendance"
    assert data["data"]["export"] is None
    assert "nothing to download" in data["answer"]


@pytest.mark.asyncio
async def test_natural_language_full_date_routes_to_daily_tool(client):
    headers = await _setup_teacher(client)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    day, month, year = today.split("-")[2], today.split("-")[1], today.split("-")[0]
    month_name = datetime(int(year), int(month), 1).strftime("%B")
    data = await _chat(client, headers, f"Show attendance for {int(day)} {month_name} {year}")
    assert data["tool_used"] == "get_daily_attendance"
    assert data["data"]["date"] == today
    assert data["data"]["total"] == 5


@pytest.mark.asyncio
async def test_numeric_date_routes_to_daily_tool_indian_convention(client):
    headers = await _setup_teacher(client)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    day, month = today.split("-")[2], today.split("-")[1]
    data = await _chat(client, headers, f"Show attendance for {day}/{month}/2026")
    assert data["tool_used"] == "get_daily_attendance"
    assert data["data"]["date"] == today


@pytest.mark.asyncio
async def test_month_query_routes_to_monthly_report(client):
    headers = await _setup_teacher(client)
    now = datetime.now(timezone.utc)
    data = await _chat(client, headers, "Show attendance for September")
    assert data["tool_used"] == "get_monthly_report"
    assert data["data"]["month"] == f"{now.year:04d}-09"


@pytest.mark.asyncio
async def test_low_attendance_wording_routes_to_threshold_tool(client):
    headers = await _setup_teacher(client)
    data = await _chat(client, headers, "Which students have low attendance?")
    assert data["tool_used"] == "get_low_attendance_students"
    names = {s["name"] for s in data["data"]}
    assert "Sagar Singh" in names
    assert "Prabin Gartia" in names


@pytest.mark.asyncio
async def test_attendance_summary_routes_and_aggregates(client):
    headers = await _setup_teacher(client)
    data = await _chat(client, headers, "Give me the attendance summary")
    assert data["tool_used"] == "get_attendance_summary"
    assert data["data"]["total_sessions"] == 3
    assert data["data"]["total_students"] == 3
    assert data["data"]["total_records"] == 5
    assert data["data"]["present"] == 3
    assert data["data"]["absent"] == 2
    assert data["data"]["attendance_percentage"] == 60.0


@pytest.mark.asyncio
async def test_class_attendance_by_name(client):
    headers = await _setup_teacher(client)
    data = await _chat(client, headers, "What is the attendance of CSE?")
    assert data["tool_used"] == "get_class_attendance_by_name"
    assert data["data"]["class_name"] == "CSE"
    assert data["data"]["attendance_percentage"] == 75.0


@pytest.mark.asyncio
async def test_subject_attendance_by_name(client):
    headers = await _setup_teacher(client)
    data = await _chat(client, headers, "What is the attendance of Data Structures?")
    assert data["tool_used"] == "get_subject_attendance_by_name"
    assert data["data"]["subject_name"] == "Data Structures"
    assert data["data"]["attendance_percentage"] == 100.0


@pytest.mark.asyncio
async def test_export_phrase_9_slash_11_is_understood(client):
    """The exact phrasing from the bug report must parse as an export intent,
    not fall back to 'couldn't determine'."""
    from app.ai.intents import detect_export

    intent = detect_export("can you create the excel sheet of attendance of 9/11/2026")
    assert intent is not None
    assert intent.intent == "export_attendance"
    assert intent.format == "xlsx"
    # Indian convention: 9/11/2026 -> 9 November 2026
    assert intent.date == "2026-11-09"

    headers = await _setup_teacher(client)
    data = await _chat(client, headers, "can you create the excel sheet of attendance of 9/11/2026")
    assert data["tool_used"] == "export_attendance"
    assert "couldn't determine" not in data["answer"]


@pytest.mark.asyncio
async def test_class_attendance_query_never_leaks_other_teacher(client):
    headers = await _setup_teacher(client)

    other_token = await _register_and_login(client, "Name Confusion", _next_email(), PASSWORD)
    other_headers = _headers(other_token)
    await _create_class(client, other_headers, "CSE")

    data = await _chat(client, headers, "What is the attendance of CSE?")
    assert data["tool_used"] == "get_class_attendance_by_name"
    assert data["data"]["attendance_percentage"] == 75.0
    # The same class name owned by another teacher must resolve to their empty
    # CSE (0 records), not this teacher's data.
    other_data = await _chat(client, other_headers, "What is the attendance of CSE?")
    assert other_data["tool_used"] == "get_class_attendance_by_name"
    assert other_data["data"]["total_records"] == 0


@pytest.mark.asyncio
async def test_demo_account_isolation_from_personal_teacher(client, monkeypatch):
    from app.config import settings
    from app.database import get_database

    monkeypatch.setattr(settings, "DEMO_MODE", True)

    headers = await _setup_teacher(client)

    db = get_database()
    demo_email = "demo@attendvortex.local"
    existing = await db.users.find_one({"email": demo_email})
    if existing is None:
        result = await db.users.insert_one(
            {
                "name": "Demo Teacher",
                "email": demo_email,
                "password_hash": "demo",
                "role": "teacher",
                "is_active": True,
            }
        )
        demo_id = str(result.inserted_id)
        await db.classes.insert_one(
            {
                "name": "DEMO CLASS ONLY",
                "semester": 1,
                "section": "A",
                "academic_year": "2026-27",
                "teacher_id": demo_id,
            }
        )

    demo_login = await client.post("/api/v1/auth/demo")
    assert demo_login.status_code == 200, demo_login.text
    demo_headers = _headers(demo_login.json()["data"]["access_token"])

    demo_data = await _chat(client, demo_headers, "How many classes do I have?")
    assert len(demo_data["data"]) == 1
    assert demo_data["data"][0]["name"] == "DEMO CLASS ONLY"

    personal_data = await _chat(client, headers, "How many classes do I have?")
    assert len(personal_data["data"]) == 2
    assert all(c["name"] != "DEMO CLASS ONLY" for c in personal_data["data"])


@pytest.mark.asyncio
async def test_timeout_returns_labeled_fallback_with_data(client, monkeypatch):
    async def fake_timeout(messages):
        return "AI request timed out. Please try again."

    monkeypatch.setattr(assistant_service.llm_client, "chat", fake_timeout)

    headers = await _setup_teacher(client)
    data = await _chat(client, headers, "Show me today's attendance.")
    assert data["tool_used"] == "get_today_attendance"
    assert data["ai_unavailable"] is True
    assert "timed out" in data["answer"]
    assert "data directly" in data["answer"]
    assert data["data"]["total"] == 5


@pytest.mark.asyncio
async def test_export_intent_is_isolated_between_teachers(client):
    headers = await _setup_teacher(client)

    other_token = await _register_and_login(client, "Export Isol Teacher", _next_email(), PASSWORD)
    other_headers = _headers(other_token)
    other_class = await _create_class(client, other_headers, "ISODEMO")
    other_subject = await _create_subject(client, other_headers, other_class, "IS001", "Isolation Demo")
    other_student = await _create_student(client, other_headers, other_class, "ISO001", "Isolated Student")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    sess = await client.post(
        "/api/v1/attendance/sessions",
        json={"class_id": other_class, "subject_id": other_subject, "date": today},
        headers=other_headers,
    )
    assert sess.status_code == 200
    session_id = sess.json()["data"]["id"]
    bulk = await client.post(
        f"/api/v1/attendance/sessions/{session_id}/bulk",
        json={"records": [{"student_id": other_student, "status": "present"}]},
        headers=other_headers,
    )
    assert bulk.status_code == 200

    day, month = today.split("-")[2], today.split("-")[1]
    data = await _chat(client, headers, f"Create the Excel sheet of attendance for {day}/{month}/2026")
    assert data["tool_used"] == "export_attendance"
    assert data["data"]["export"]["row_count"] == 5


@pytest.mark.asyncio
async def test_health_endpoint_public_and_secret_free(client, monkeypatch):
    async def fake_health():
        return {
            "available": True,
            "provider": "ollama",
            "model": "llama3",
            "reason": None,
        }

    monkeypatch.setattr(assistant_service.llm_client, "health", fake_health)

    resp = await client.get("/api/v1/ai/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["available"] is True
    assert "base_url" not in body["data"]
    assert "api_key" not in json.dumps(body).lower()


@pytest.mark.asyncio
async def test_health_reflects_missing_config(client, monkeypatch):
    async def fake_health():
        return {
            "available": False,
            "provider": "ollama",
            "model": "llama3",
            "reason": "OLLAMA_BASE_URL is not configured.",
        }

    monkeypatch.setattr(assistant_service.llm_client, "health", fake_health)

    resp = await client.get("/api/v1/ai/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["available"] is False
    assert body["data"]["reason"]