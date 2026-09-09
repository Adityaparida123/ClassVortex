import pytest

PERSONAL_EMAIL = "isolation_personal@example.com"
PERSONAL_PASSWORD = "personalpass123"
DEMO_EMAIL = "demo@attendvortex.local"
DEMO_PASSWORD = "DemoAttendVortex2026!"


async def _register_and_login(client, name, email, password, role="teacher"):
    await client.post("/api/v1/auth/register", json={
        "name": name,
        "email": email,
        "password": password,
        "role": role,
    })
    login = await client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password,
    })
    assert login.status_code == 200
    return login.json()["data"]["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


async def _create_class(client, headers, name="Class"):
    resp = await client.post("/api/v1/classes", json={
        "name": name,
        "semester": 1,
        "section": "A",
        "academic_year": "2026-27",
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


async def _create_subject(client, headers, class_id, code, name):
    resp = await client.post("/api/v1/subjects", json={
        "name": name,
        "code": code,
        "class_id": class_id,
        "teacher_id": "ignored",
    }, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["id"]


@pytest.mark.asyncio
async def test_class_isolation_between_accounts(client):
    personal_token = await _register_and_login(client, "Personal User", PERSONAL_EMAIL, PERSONAL_PASSWORD)
    demo_token = await _register_and_login(client, "Demo User", DEMO_EMAIL, DEMO_PASSWORD)
    personal_headers = _headers(personal_token)
    demo_headers = _headers(demo_token)

    personal_class = await _create_class(client, personal_headers, "Personal Class A")
    demo_class = await _create_class(client, demo_headers, "Demo Class A")

    personal_list = (await client.get("/api/v1/classes", headers=personal_headers)).json()["data"]
    demo_list = (await client.get("/api/v1/classes", headers=demo_headers)).json()["data"]

    personal_ids = {c["id"] for c in personal_list}
    demo_ids = {c["id"] for c in demo_list}

    assert personal_class in personal_ids
    assert demo_class in demo_ids
    assert demo_class not in personal_ids
    assert personal_class not in demo_ids


@pytest.mark.asyncio
async def test_cross_user_class_access_returns_404(client):
    personal_token = await _register_and_login(client, "Personal User B", "isolation_b@example.com", PERSONAL_PASSWORD)
    demo_token = await _register_and_login(client, "Demo User B", "demo_b@attendvortex.local", DEMO_PASSWORD)
    personal_headers = _headers(personal_token)
    demo_headers = _headers(demo_token)

    personal_class = await _create_class(client, personal_headers, "Personal Class B")
    demo_class = await _create_class(client, demo_headers, "Demo Class B")

    resp = await client.get(f"/api/v1/classes/{demo_class}", headers=personal_headers)
    assert resp.status_code == 404
    resp = await client.get(f"/api/v1/classes/{personal_class}", headers=demo_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_student_isolation_between_accounts(client):
    personal_token = await _register_and_login(client, "Personal User C", "isolation_c@example.com", PERSONAL_PASSWORD)
    demo_token = await _register_and_login(client, "Demo User C", "demo_c@attendvortex.local", DEMO_PASSWORD)
    personal_headers = _headers(personal_token)
    demo_headers = _headers(demo_token)

    personal_class = await _create_class(client, personal_headers, "Personal Class C")
    demo_class = await _create_class(client, demo_headers, "Demo Class C")

    personal_student = await _create_student(client, personal_headers, personal_class, "ISO001", "Personal Student")
    demo_student = await _create_student(client, demo_headers, demo_class, "ISODEMO01", "Demo Student")

    personal_list = (await client.get("/api/v1/students", headers=personal_headers)).json()["data"]
    demo_list = (await client.get("/api/v1/students", headers=demo_headers)).json()["data"]

    personal_ids = {s["id"] for s in personal_list}
    demo_ids = {s["id"] for s in demo_list}

    assert personal_student in personal_ids
    assert demo_student in demo_ids
    assert demo_student not in personal_ids
    assert personal_student not in demo_ids


@pytest.mark.asyncio
async def test_cross_user_student_access_returns_404(client):
    personal_token = await _register_and_login(client, "Personal User D", "isolation_d@example.com", PERSONAL_PASSWORD)
    demo_token = await _register_and_login(client, "Demo User D", "demo_d@attendvortex.local", DEMO_PASSWORD)
    personal_headers = _headers(personal_token)
    demo_headers = _headers(demo_token)

    personal_class = await _create_class(client, personal_headers, "Personal Class D")
    demo_class = await _create_class(client, demo_headers, "Demo Class D")

    personal_student = await _create_student(client, personal_headers, personal_class, "ISO002", "Personal Student D")
    demo_student = await _create_student(client, demo_headers, demo_class, "ISODEMO02", "Demo Student D")

    resp = await client.get(f"/api/v1/students/{demo_student}", headers=personal_headers)
    assert resp.status_code == 404
    resp = await client.get(f"/api/v1/students/{personal_student}", headers=demo_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_subject_isolation_and_create(client):
    personal_token = await _register_and_login(client, "Personal User E", "isolation_e@example.com", PERSONAL_PASSWORD)
    demo_token = await _register_and_login(client, "Demo User E", "demo_e@attendvortex.local", DEMO_PASSWORD)
    personal_headers = _headers(personal_token)
    demo_headers = _headers(demo_token)

    personal_class = await _create_class(client, personal_headers, "Personal Class E")
    demo_class = await _create_class(client, demo_headers, "Demo Class E")

    personal_subject = await _create_subject(client, personal_headers, personal_class, "ISOSUB01", "Personal Subject")
    demo_subject = await _create_subject(client, demo_headers, demo_class, "ISOSUB02", "Demo Subject")

    personal_list = (await client.get("/api/v1/subjects", headers=personal_headers)).json()["data"]
    demo_list = (await client.get("/api/v1/subjects", headers=demo_headers)).json()["data"]

    personal_ids = {s["id"] for s in personal_list}
    demo_ids = {s["id"] for s in demo_list}

    assert personal_subject in personal_ids
    assert demo_subject in demo_ids
    assert demo_subject not in personal_ids
    assert personal_subject not in demo_ids

    # Cannot create a subject attached to another user's class
    resp = await client.post("/api/v1/subjects", json={
        "name": "Intruder Subject",
        "code": "ISOSUB99",
        "class_id": demo_class,
        "teacher_id": "ignored",
    }, headers=personal_headers)
    assert resp.status_code == 404

    # Subject creation still works for an owned class
    extra = await client.post("/api/v1/subjects", json={
        "name": "Extra Subject",
        "code": "ISOSUB03",
        "class_id": personal_class,
        "teacher_id": "ignored",
    }, headers=personal_headers)
    assert extra.status_code == 200


@pytest.mark.asyncio
async def test_attendance_session_isolation_and_class_derivation(client):
    personal_token = await _register_and_login(client, "Personal User F", "isolation_f@example.com", PERSONAL_PASSWORD)
    demo_token = await _register_and_login(client, "Demo User F", "demo_f@attendvortex.local", DEMO_PASSWORD)
    personal_headers = _headers(personal_token)
    demo_headers = _headers(demo_token)

    personal_class = await _create_class(client, personal_headers, "Personal Class F")
    demo_class = await _create_class(client, demo_headers, "Demo Class F")

    personal_subject = await _create_subject(client, personal_headers, personal_class, "ISOSUBF1", "Personal Subject F")
    demo_subject = await _create_subject(client, demo_headers, demo_class, "ISOSUBF2", "Demo Subject F")

    sess = await client.post("/api/v1/attendance/sessions", json={
        "class_id": personal_class,
        "subject_id": personal_subject,
        "date": "2026-09-10",
    }, headers=personal_headers)
    assert sess.status_code == 200
    session_id = sess.json()["data"]["id"]

    # Demo cannot see personal sessions
    demo_sessions = (await client.get("/api/v1/attendance/sessions", headers=demo_headers)).json()["data"]
    assert session_id not in {s["id"] for s in demo_sessions}

    # Demo cannot fetch the personal session by id
    resp = await client.get(f"/api/v1/attendance/sessions/{session_id}", headers=demo_headers)
    assert resp.status_code == 404

    # Attempting to create a session with mismatched class_id (subject's class is personal_class)
    bad = await client.post("/api/v1/attendance/sessions", json={
        "class_id": demo_class,
        "subject_id": personal_subject,
        "date": "2026-09-10",
    }, headers=personal_headers)
    assert bad.status_code == 400


@pytest.mark.asyncio
async def test_reports_isolated(client):
    personal_token = await _register_and_login(client, "Personal User G", "isolation_g@example.com", PERSONAL_PASSWORD)
    demo_token = await _register_and_login(client, "Demo User G", "demo_g@attendvortex.local", DEMO_PASSWORD)
    personal_headers = _headers(personal_token)
    demo_headers = _headers(demo_token)

    personal_class = await _create_class(client, personal_headers, "Personal Class G")
    demo_class = await _create_class(client, demo_headers, "Demo Class G")

    resp = await client.get(f"/api/v1/reports/class/{demo_class}", headers=personal_headers)
    assert resp.status_code == 404
    resp = await client.get(f"/api/v1/reports/class/{personal_class}", headers=demo_headers)
    assert resp.status_code == 404

    daily_own = await client.get(f"/api/v1/reports/daily?class_id={personal_class}", headers=personal_headers)
    assert daily_own.status_code == 200


@pytest.mark.asyncio
async def test_demo_login_works(client):
    await _register_and_login(client, "Demo Login User", DEMO_EMAIL, DEMO_PASSWORD)
    login = await client.post("/api/v1/auth/login", json={
        "email": DEMO_EMAIL,
        "password": DEMO_PASSWORD,
    })
    assert login.status_code == 200
    assert "access_token" in login.json()["data"]