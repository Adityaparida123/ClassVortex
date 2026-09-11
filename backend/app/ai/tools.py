from datetime import datetime, timezone
from bson import ObjectId
from app.database import get_database
from app.utils.helpers import serialize_id


async def find_student_attendance(query_text: str, teacher_id: str) -> dict:
    db = get_database()
    if db is None:
        return None

    # Build candidate name/roll tokens. A student matches if any query token is
    # an exact roll number, or matches any word of the student's name.
    tokens = [
        t.strip().lower()
        for t in query_text.replace("'", " ").replace("?", " ").split()
        if len(t.strip()) > 1
    ] or []
    # Skip obvious filler words so "what is my attendance" does not match
    # a random student by a short token like "is" or "my".
    filler = {
        "what", "which", "who", "is", "are", "the", "a", "an", "of", "for",
        "with", "show", "me", "my", "list", "all", "has", "have", "having",
        "their", "and", "attendance", "student", "students", "class", "classes",
        "subject", "subjects", "in", "on", "at", "from", "to", "lowest",
        "below", "tell", "how", "many", "does", "do", "today", "today's",
        "percentage", "report", "summary", "update", "per", "cent", "please",
        "can", "you", "could", "give", "get", "find", "about",
    }
    search_tokens = [t for t in tokens if t not in filler]
    if not search_tokens:
        return None

    async for student in db.students.find({"is_active": True, "teacher_id": teacher_id}):
        st_name = (student.get("name", "") or "").lower()
        st_roll = (student.get("roll_number", "") or "").lower()
        name_words = set(st_name.split())
        # Accept a match if any search token is a full word of the name, or the
        # (possibly multi-token) query contains the full student name, or the
        # token equals the roll number.
        if any(token in name_words for token in search_tokens):
            matched = True
        elif st_name in query_text.lower():
            matched = True
        elif any(token == st_roll for token in search_tokens):
            matched = True
        else:
            matched = False
        if not matched:
            continue
        sid = str(student["_id"])
        total = await db.attendance_records.count_documents(
            {"student_id": sid, "teacher_id": teacher_id}
        )
        present = await db.attendance_records.count_documents(
            {"student_id": sid, "teacher_id": teacher_id, "status": "present"}
        )
        late = await db.attendance_records.count_documents(
            {"student_id": sid, "teacher_id": teacher_id, "status": "late"}
        )
        absent = await db.attendance_records.count_documents(
            {"student_id": sid, "teacher_id": teacher_id, "status": "absent"}
        )
        excused = await db.attendance_records.count_documents(
            {"student_id": sid, "teacher_id": teacher_id, "status": "excused"}
        )
        present_for_pct = present + late + excused
        pct = round((present_for_pct / total * 100), 2) if total > 0 else 0.0
        return {
            "student": serialize_id(student),
            "total": total,
            "present": present,
            "late": late,
            "absent": absent,
            "excused": excused,
            "percentage": pct,
        }
    return None


async def get_student_attendance(student_id: str, teacher_id: str) -> list:
    db = get_database()
    if db is None:
        return []
    records = []
    async for record in db.attendance_records.find(
        {"student_id": student_id, "teacher_id": teacher_id}
    ):
        records.append(serialize_id(record))
    return records


async def get_all_classes(teacher_id: str) -> list:
    db = get_database()
    if db is None:
        return []
    classes = []
    async for cls in db.classes.find({"teacher_id": teacher_id}):
        classes.append(serialize_id(cls))
    return classes


async def get_class_attendance(class_id: str, teacher_id: str) -> list:
    db = get_database()
    if db is None:
        return []
    sessions = []
    async for session in db.attendance_sessions.find(
        {"class_id": class_id, "teacher_id": teacher_id}
    ):
        sessions.append(serialize_id(session))
    return sessions


async def get_all_subjects(teacher_id: str) -> list:
    db = get_database()
    if db is None:
        return []
    subjects = []
    async for subject in db.subjects.find({"teacher_id": teacher_id, "is_active": {"$ne": False}}):
        subjects.append(serialize_id(subject))
    return subjects


async def get_subject_attendance(subject_id: str, teacher_id: str) -> list:
    db = get_database()
    if db is None:
        return []
    sessions = []
    async for session in db.attendance_sessions.find(
        {"subject_id": subject_id, "teacher_id": teacher_id}
    ):
        sessions.append(serialize_id(session))
    return sessions


async def get_absent_students(teacher_id: str) -> list:
    db = get_database()
    if db is None:
        return []
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    records = []
    async for sess in db.attendance_sessions.find(
        {"date": today_str, "teacher_id": teacher_id}
    ):
        sess_id = str(sess["_id"])
        async for record in db.attendance_records.find(
            {"session_id": sess_id, "teacher_id": teacher_id, "status": "absent"}
        ):
            rec_data = serialize_id(record)
            try:
                st = await db.students.find_one(
                    {"_id": ObjectId(record["student_id"]), "teacher_id": teacher_id}
                )
                if st:
                    rec_data["student_name"] = st.get("name")
                    rec_data["roll_number"] = st.get("roll_number")
                    rec_data["class_id"] = str(st.get("class_id", ""))
            except Exception:
                pass
            records.append(rec_data)

    if not records:
        async for record in db.attendance_records.find(
            {"status": "absent", "teacher_id": teacher_id}
        ).sort("_id", -1).limit(20):
            rec_data = serialize_id(record)
            try:
                st = await db.students.find_one(
                    {"_id": ObjectId(record["student_id"]), "teacher_id": teacher_id}
                )
                if st:
                    rec_data["student_name"] = st.get("name")
                    rec_data["roll_number"] = st.get("roll_number")
                    rec_data["class_id"] = str(st.get("class_id", ""))
            except Exception:
                pass
            records.append(rec_data)
    return records


async def get_low_attendance_students(threshold: float, teacher_id: str) -> list:
    db = get_database()
    if db is None:
        return []
    students = []
    async for student in db.students.find({"is_active": True, "teacher_id": teacher_id}):
        student_data = serialize_id(student)
        sid = student_data["id"]
        total = await db.attendance_records.count_documents(
            {"student_id": sid, "teacher_id": teacher_id}
        )
        if total == 0:
            continue
        present = await db.attendance_records.count_documents(
            {"student_id": sid, "teacher_id": teacher_id, "status": "present"}
        )
        late = await db.attendance_records.count_documents(
            {"student_id": sid, "teacher_id": teacher_id, "status": "late"}
        )
        excused = await db.attendance_records.count_documents(
            {"student_id": sid, "teacher_id": teacher_id, "status": "excused"}
        )
        present_for_pct = present + late + excused
        percentage = (present_for_pct / total * 100)
        if percentage < threshold:
            student_data["attendance_percentage"] = round(percentage, 2)
            student_data["total_sessions"] = total
            student_data["present_sessions"] = present_for_pct
            students.append(student_data)

    def sort_key(s):
        return s.get("attendance_percentage", 0.0)

    students.sort(key=sort_key)
    return students


async def get_student_attendance_ranking(teacher_id: str) -> list:
    """Rank every active student of the teacher by attendance percentage."""
    db = get_database()
    if db is None:
        return []
    results = []
    async for student in db.students.find({"is_active": True, "teacher_id": teacher_id}):
        student_data = serialize_id(student)
        sid = student_data["id"]
        total = await db.attendance_records.count_documents(
            {"student_id": sid, "teacher_id": teacher_id}
        )
        if total == 0:
            student_data["attendance_percentage"] = 0.0
            student_data["total_sessions"] = 0
            student_data["present_sessions"] = 0
            results.append(student_data)
            continue
        present = await db.attendance_records.count_documents(
            {"student_id": sid, "teacher_id": teacher_id, "status": "present"}
        )
        late = await db.attendance_records.count_documents(
            {"student_id": sid, "teacher_id": teacher_id, "status": "late"}
        )
        excused = await db.attendance_records.count_documents(
            {"student_id": sid, "teacher_id": teacher_id, "status": "excused"}
        )
        present_for_pct = present + late + excused
        student_data["attendance_percentage"] = round(present_for_pct / total * 100, 2)
        student_data["total_sessions"] = total
        student_data["present_sessions"] = present_for_pct
        results.append(student_data)

    results.sort(key=lambda s: s.get("attendance_percentage", 0.0))
    return results


async def get_class_attendance_comparison(teacher_id: str) -> list:
    """Aggregate attendance percentages per class for the authenticated teacher.

    A class's percentage is the average of its students' attendance percentages,
    computed from actual attendance_records (present/late/excused count as
    attended, absent does not).
    """
    db = get_database()
    if db is None:
        return []
    # Ensure the caller truly owns each class before aggregating.
    class_ids = []
    class_list = []
    async for cls in db.classes.find({"teacher_id": teacher_id}):
        class_ids.append(str(cls["_id"]))
        class_list.append(serialize_id(cls))
    if not class_ids:
        return []

    class_by_id = {c["id"]: c for c in class_list}
    per_class = {
        cid: {"total": 0, "attended": 0, "students": set()} for cid in class_ids
    }
    class_ids_set = set(class_ids)

    # Map owned sessions to their class so records can be attributed without
    # ever touching another teacher's data.
    session_to_class = {}
    async for sess in db.attendance_sessions.find(
        {"teacher_id": teacher_id}, {"class_id": 1}
    ):
        cid = str(sess.get("class_id") or "")
        if cid in class_ids_set:
            session_to_class[str(sess["_id"])] = cid

    async for student in db.students.find({"teacher_id": teacher_id, "is_active": True}):
        cid = str(student.get("class_id") or "")
        if cid in class_ids_set:
            per_class[cid]["students"].add(str(student["_id"]))

    async for record in db.attendance_records.find(
        {"teacher_id": teacher_id},
        {"student_id": 1, "status": 1, "session_id": 1},
    ):
        sid = str(record.get("session_id") or "")
        cid = session_to_class.get(sid)
        if cid is None:
            continue
        per_class[cid]["total"] += 1
        if record.get("status") in ("present", "late", "excused"):
            per_class[cid]["attended"] += 1

    results = []
    for cid in class_ids:
        meta = class_by_id[cid]
        data = per_class[cid]
        pct = round(data["attended"] / data["total"] * 100, 2) if data["total"] > 0 else 0.0
        results.append(
            {
                "class_id": cid,
                "class_name": meta.get("name", "Unknown class"),
                "attendance_percentage": pct,
                "total_records": data["total"],
                "student_count": len(data["students"]),
            }
        )

    results.sort(key=lambda c: c["attendance_percentage"])
    return results


async def get_subject_attendance_comparison(teacher_id: str) -> list:
    """Aggregate attendance percentages per subject for the authenticated teacher."""
    db = get_database()
    if db is None:
        return []
    subject_ids = []
    subject_list = []
    async for subject in db.subjects.find(
        {"teacher_id": teacher_id, "is_active": {"$ne": False}}
    ):
        subject_ids.append(str(subject["_id"]))
        subject_list.append(serialize_id(subject))
    if not subject_ids:
        return []

    subject_by_id = {s["id"]: s for s in subject_list}
    per_subject = {sid: {"total": 0, "attended": 0} for sid in subject_ids}
    subject_ids_set = set(subject_ids)

    # Map owned sessions to their subject so records can be attributed without
    # ever touching another teacher's data.
    session_to_subject = {}
    async for sess in db.attendance_sessions.find(
        {"teacher_id": teacher_id}, {"subject_id": 1}
    ):
        sid = str(sess.get("subject_id") or "")
        if sid in subject_ids_set:
            session_to_subject[str(sess["_id"])] = sid

    async for record in db.attendance_records.find(
        {"teacher_id": teacher_id},
        {"student_id": 1, "status": 1, "session_id": 1},
    ):
        sid = session_to_subject.get(str(record.get("session_id") or ""))
        if sid is None:
            continue
        per_subject[sid]["total"] += 1
        if record.get("status") in ("present", "late", "excused"):
            per_subject[sid]["attended"] += 1

    results = []
    for sid in subject_ids:
        meta = subject_by_id[sid]
        data = per_subject[sid]
        pct = round(data["attended"] / data["total"] * 100, 2) if data["total"] > 0 else 0.0
        class_name = ""
        try:
            cls = await db.classes.find_one(
                {"_id": ObjectId(meta.get("class_id")), "teacher_id": teacher_id}
            )
            if cls:
                class_name = cls.get("name", "")
        except Exception:
            pass
        results.append(
            {
                "subject_id": sid,
                "subject_name": meta.get("name", "Unknown subject"),
                "subject_code": meta.get("code", "") or meta.get("subject_code", ""),
                "class_id": str(meta.get("class_id") or ""),
                "class_name": class_name,
                "attendance_percentage": pct,
                "total_records": data["total"],
            }
        )

    results.sort(key=lambda s: s["attendance_percentage"])
    return results


async def get_class_students(class_id: str, teacher_id: str) -> dict:
    db = get_database()
    if db is None:
        return {"class_id": class_id, "class_name": "Unknown", "students": [], "student_count": 0}
    try:
        cls = await db.classes.find_one({"_id": ObjectId(class_id), "teacher_id": teacher_id})
    except Exception:
        cls = None
    if not cls:
        return {"class_id": class_id, "class_name": "Unknown", "students": [], "student_count": 0}

    students = []
    async for student in db.students.find(
        {"class_id": class_id, "teacher_id": teacher_id, "is_active": True}
    ):
        students.append(serialize_id(student))

    students.sort(key=lambda s: s.get("name", ""))
    return {
        "class_id": class_id,
        "class_name": cls.get("name", "Unknown"),
        "students": students,
        "student_count": len(students),
    }


async def get_students_by_class_name(class_name: str, teacher_id: str) -> dict:
    """Resolve a class by name (owned by the teacher) and return its students."""
    db = get_database()
    if db is None:
        return None
    name_lower = class_name.strip().lower()
    async for cls in db.classes.find({"teacher_id": teacher_id}):
        if (cls.get("name") or "").strip().lower() == name_lower:
            return await get_class_students(str(cls["_id"]), teacher_id)
    return None


async def get_total_student_count(teacher_id: str) -> int:
    db = get_database()
    if db is None:
        return 0
    return await db.students.count_documents(
        {"teacher_id": teacher_id, "is_active": True}
    )


async def get_today_attendance(teacher_id: str) -> dict:
    """Return today's active session(s) plus their attendance records."""
    db = get_database()
    if db is None:
        return {"date": None, "sessions": [], "present": 0, "absent": 0, "late": 0, "excused": 0, "total": 0}
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    sessions = []
    present = absent = late = excused = total = 0
    async for sess in db.attendance_sessions.find(
        {"date": today_str, "teacher_id": teacher_id}
    ):
        sess_id = str(sess["_id"])
        session_data = serialize_id(sess)
        records = []
        async for record in db.attendance_records.find(
            {"session_id": sess_id, "teacher_id": teacher_id}
        ):
            rec_data = serialize_id(record)
            status = rec_data.get("status", "")
            if status == "present":
                present += 1
            elif status == "absent":
                absent += 1
            elif status == "late":
                late += 1
            elif status == "excused":
                excused += 1
            total += 1
            try:
                st = await db.students.find_one(
                    {"_id": ObjectId(record["student_id"]), "teacher_id": teacher_id}
                )
                if st:
                    rec_data["student_name"] = st.get("name")
                    rec_data["roll_number"] = st.get("roll_number")
            except Exception:
                pass
            records.append(rec_data)

        class_name = ""
        try:
            cls = await db.classes.find_one(
                {"_id": ObjectId(sess.get("class_id")), "teacher_id": teacher_id}
            )
            if cls:
                class_name = cls.get("name", "")
        except Exception:
            pass
        subject_name = ""
        try:
            subject = await db.subjects.find_one(
                {"_id": ObjectId(sess.get("subject_id")), "teacher_id": teacher_id}
            )
            if subject:
                subject_name = subject.get("name", "")
        except Exception:
            pass

        session_data["class_name"] = class_name
        session_data["subject_name"] = subject_name
        session_data["records"] = records
        sessions.append(session_data)

    return {
        "date": today_str,
        "sessions": sessions,
        "present": present,
        "absent": absent,
        "late": late,
        "excused": excused,
        "total": total,
    }


async def get_monthly_report(month: str, teacher_id: str) -> dict:
    if not month:
        month = datetime.now(timezone.utc).strftime("%Y-%m")

    db = get_database()
    if db is None:
        return {"month": month, "total_sessions": 0}
    sessions = []
    async for session in db.attendance_sessions.find(
        {"date": {"$regex": f"^{month}"}, "teacher_id": teacher_id}
    ):
        sessions.append(serialize_id(session))
    return {"month": month, "total_sessions": len(sessions)}


async def get_student_details(student_id: str, teacher_id: str) -> dict:
    db = get_database()
    if db is None:
        return None
    try:
        student = await db.students.find_one(
            {"_id": ObjectId(student_id), "teacher_id": teacher_id}
        )
    except Exception:
        return None
    return serialize_id(student) if student else None