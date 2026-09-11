import json
from app.ai.llm_client import llm_client
from app.ai.prompts import SYSTEM_PROMPT, TOOL_DESCRIPTIONS
from app.ai import tools


def _contains_query(message_lower: str, phrases) -> bool:
    return any(phrase in message_lower for phrase in phrases)


async def _route_tool(message: str, teacher_id: str) -> dict:
    """Determine which tool to run based on the user's intent.

    Returns {"tool_used": str|None, "data": ...}. When no matching intent is
    found, both tool_used and data are None so the caller can produce a helpful
    "I couldn't determine" response instead of guessing.
    """
    message_lower = " " + message.lower().strip() + " "

    # --- Student-specific queries (name / roll number present) ---
    st_info = await tools.find_student_attendance(message, teacher_id)
    if st_info is not None:
        return {"tool_used": "find_student_attendance", "data": st_info}

    # --- Absent today / absences ---
    if _contains_query(
        message_lower,
        [
            "who was absent",
            "who is absent",
            "who were absent",
            "who are absent",
            "all absent",
            "absentees",
            "absent today",
            "absent students",
            "absentees list",
            "not present in class",
            "not in class",
        ],
    ):
        data = await tools.get_absent_students(teacher_id)
        return {"tool_used": "get_absent_students", "data": data}

    # --- Today's attendance ---
    if _contains_query(
        message_lower,
        ["today's attendance", "today attendance", "attendance today", "today's class", "recorded today", "session today", "today session"],
    ):
        data = await tools.get_today_attendance(teacher_id)
        return {"tool_used": "get_today_attendance", "data": data}

    # --- Monthly report ---
    if _contains_query(message_lower, ["monthly report", "report for this month", "report of this month", "month's report"]):
        data = await tools.get_monthly_report("", teacher_id)
        return {"tool_used": "get_monthly_report", "data": data}

    # --- Below-threshold students ---
    if _contains_query(message_lower, ["below 75", "less than 75", "under 75", "below 75%", "less than 75%"]):
        data = await tools.get_low_attendance_students(75.0, teacher_id)
        return {"tool_used": "get_low_attendance_students", "data": data}

    # --- Class & subject listing together ---
    if _contains_query(
        message_lower,
        [
            "all the subjects and classes",
            "all the classes and subjects",
            "subjects and classes we have",
            "classes and subjects we have",
            "list classes and subjects",
            "list subjects and classes",
            "all subjects and classes",
            "all classes and subjects",
            "classes and subjects",
            "subjects and classes",
        ],
    ):
        classes = await tools.get_all_classes(teacher_id)
        subjects = await tools.get_all_subjects(teacher_id)
        return {
            "tool_used": "get_classes_and_subjects",
            "data": {"classes": classes, "subjects": subjects},
        }

    # --- Class-level questions ---
    if _contains_query(
        message_lower,
        [
            "which class has the lowest",
            "which class has lowest",
            "which class has the highest",
            "which class has highest",
            "best class",
            "worst class",
            "lowest attendance class",
            "highest attendance class",
            "class with the lowest",
            "class with the highest",
            "compare classes",
            "compare my classes",
            "compare the classes",
            "class attendance comparison",
        ],
    ):
        data = await tools.get_class_attendance_comparison(teacher_id)
        return {"tool_used": "get_class_attendance_comparison", "data": data}

    # "class" + "attendance" or "attendance" + specific class without a name
    # We cannot resolve a specific single class here without a class name, so
    # fall back to comparing classes only when the question is generic.
    # (see above)

    # --- Subject-level questions ---
    if _contains_query(
        message_lower,
        [
            "which subject has the lowest",
            "which subject has lowest",
            "which subject has the highest",
            "which subject has highest",
            "lowest attendance subject",
            "highest attendance subject",
            "subject with the lowest",
            "subject with the highest",
            "compare subjects",
            "compare my subjects",
            "compare the subjects",
            "subject attendance comparison",
            "subject with best",
            "subject with worst",
        ],
    ):
        data = await tools.get_subject_attendance_comparison(teacher_id)
        return {"tool_used": "get_subject_attendance_comparison", "data": data}

    # --- Student-level comparison (lowest / highest attendance) ---
    if _contains_query(
        message_lower,
        [
            "which student has the lowest",
            "which student has lowest",
            "which student has the highest",
            "which student has highest",
            "student with the lowest",
            "student with the highest",
            "lowest attendance student",
            "highest attendance student",
            "lowest attendance",
            "lowest attendance in",
        ],
    ):
        data = await tools.get_student_attendance_ranking(teacher_id)
        return {"tool_used": "get_student_attendance_ranking", "data": data}

    # --- Count questions ---
    if _contains_query(message_lower, ["how many"]):
        lowered = message_lower
        has_students = any(k in lowered for k in ["student", "students"])
        has_classes = any(k in lowered for k in ["class", "classes"])
        has_subjects = any(k in lowered for k in ["subject", "subjects"])

        # Prefer a specific class when the query names one (e.g. "in CSE").
        named_class = await _extract_class_name(message, teacher_id)

        if has_students and named_class is not None:
            data = await tools.get_students_by_class_name(named_class, teacher_id)
            return {"tool_used": "get_class_students", "data": data}
        if has_students:
            data = {"total_students": await tools.get_total_student_count(teacher_id)}
            return {"tool_used": "get_total_student_count", "data": data}
        if has_classes and has_subjects:
            classes = await tools.get_all_classes(teacher_id)
            subjects = await tools.get_all_subjects(teacher_id)
            return {
                "tool_used": "get_classes_and_subjects",
                "data": {"classes": classes, "subjects": subjects},
            }
        if has_classes:
            data = await tools.get_all_classes(teacher_id)
            return {"tool_used": "get_all_classes", "data": data}
        if has_subjects:
            data = await tools.get_all_subjects(teacher_id)
            return {"tool_used": "get_all_subjects", "data": data}

    # --- Class listing (individual) ---
    if _contains_query(message_lower, ["show all classes", "list all classes", "my classes", "all my classes", "list classes", "show classes", "classes do i have", "classes we have", "what classes", "class list"]):
        data = await tools.get_all_classes(teacher_id)
        return {"tool_used": "get_all_classes", "data": data}

    # --- Subject listing (individual) ---
    if _contains_query(message_lower, ["show all subjects", "list all subjects", "my subjects", "all my subjects", "list subjects", "show subjects", "subjects do i have", "subjects we have", "what subjects", "subject list"]):
        data = await tools.get_all_subjects(teacher_id)
        return {"tool_used": "get_all_subjects", "data": data}

    # --- Students in a specific class by name ---
    if _contains_query(
        message_lower,
        [
            "students in",
            "students of",
            "students from",
            "students enrolled",
            "who are in the class",
            "who is in the class",
            "class has",
            "class have",
        ],
    ):
        class_name = await _extract_class_name(message, teacher_id)
        if class_name is not None:
            data = await tools.get_students_by_class_name(class_name, teacher_id)
            return {"tool_used": "get_class_students", "data": data}

    return {"tool_used": None, "data": None}


async def _extract_class_name(message: str, teacher_id: str):
    """Return an owned class name if it appears in the message, else None."""
    try:
        classes = await tools.get_all_classes(teacher_id)
    except Exception:
        return None
    if not classes:
        return None

    message_lower = message.lower()
    best = None
    for cls in classes:
        name = cls.get("name", "")
        if name and name.lower() in message_lower:
            if best is None or len(name) > len(best):
                best = name
    return best


async def _fallback_answers(message: str) -> str:
    return (
        "I couldn't determine what attendance information you're asking for. "
        "You can ask me about classes, subjects, students, or attendance summaries. "
        'For example: "Which class has the lowest attendance?", '
        '"Which subject has the lowest attendance?", '
        '"Which student has the lowest attendance?", '
        '"Show students below 75% attendance?", or "List all my classes and subjects".'
    )


async def _fallback_tool_message(tool_used, data) -> str:
    """Natural-language response when the AI service itself is unavailable."""
    if tool_used == "find_student_attendance":
        st = data.get("student", {})
        name = st.get("name", "Student")
        roll = st.get("roll_number", "")
        pct = data.get("percentage", 0)
        tot = data.get("total", 0)
        pres = data.get("present", 0)
        return f"**{name}** ({roll}): Attendance is **{pct}%** ({pres} present out of {tot} total sessions)."
    if tool_used == "get_low_attendance_students":
        if not data:
            return "All active students currently have attendance of **75% or higher**."
        lines = [
            f"• **{s['name']}** ({s.get('roll_number', '')}): **{s.get('attendance_percentage', 0)}%** "
            f"({s.get('present_sessions', 0)}/{s.get('total_sessions', 0)} sessions)"
            for s in data
        ]
        return f"Found **{len(data)} student(s)** with attendance below 75%:\n\n" + "\n".join(lines)
    if tool_used == "get_absent_students":
        if not data:
            return "No students are marked absent today."
        names = list({s.get("student_name") for s in data if s.get("student_name")})
        if names:
            return f"Students marked absent today ({len(names)}):\n\n" + "\n".join(f"• {name}" for name in names)
        return f"Found **{len(data)} absent records** today."
    if tool_used == "get_monthly_report":
        return f"**Monthly Report ({data.get('month', '')})**: Total **{data.get('total_sessions', 0)} sessions** recorded."
    if tool_used == "get_today_attendance":
        return (
            f"**Attendance for {data.get('date', 'today')}**: {data.get('total', 0)} records "
            f"({data.get('present', 0)} present, {data.get('absent', 0)} absent, "
            f"{data.get('late', 0)} late, {data.get('excused', 0)} excused) across "
            f"{len(data.get('sessions', []))} session(s)."
        )
    if tool_used == "get_all_classes":
        if not data:
            return "You currently have no classes."
        names = [c.get("name", "Unnamed") for c in data]
        return f"Your classes ({len(names)}):\n\n" + "\n".join(f"• {name}" for name in names)
    if tool_used == "get_all_subjects":
        if not data:
            return "You currently have no subjects."
        lines = [
            f"• **{s.get('name', 'Unnamed')}**{(' (' + str(s.get('code', '') or '') + ')') if (s.get('code') or s.get('subject_code')) else ''}"
            for s in data
        ]
        return f"Your subjects ({len(lines)}):\n\n" + "\n".join(lines)
    if tool_used == "get_class_attendance_comparison":
        if not data:
            return "You currently have no classes, so there is no class attendance to compare."
        lines = [
            f"• **{c.get('class_name', 'Unknown')}**: **{c.get('attendance_percentage', 0)}%** "
            f"({c.get('total_records', 0)} records)"
            for c in data
        ]
        lowest = data[0]
        return (
            f"Class attendance comparison:\n\n" + "\n".join(lines) +
            f"\n\n**{lowest.get('class_name', 'Unknown')}** currently has the lowest attendance at "
            f"**{lowest.get('attendance_percentage', 0)}%**."
        )
    if tool_used == "get_subject_attendance_comparison":
        if not data:
            return "You currently have no subjects, so there is no subject attendance to compare."
        lines = [
            f"• **{s.get('subject_name', 'Unknown')}**{(' (' + str(s.get('subject_code') or '') + ')') if s.get('subject_code') else ''} "
            f"({s.get('class_name', '')}): **{s.get('attendance_percentage', 0)}%**"
            for s in data
        ]
        lowest = data[0]
        return (
            f"Subject attendance comparison:\n\n" + "\n".join(lines) +
            f"\n\n**{lowest.get('subject_name', 'Unknown')}** currently has the lowest attendance at "
            f"**{lowest.get('attendance_percentage', 0)}%**."
        )
    if tool_used == "get_student_attendance_ranking":
        if not data:
            return "You currently have no students with attendance records."
        lowest = data[0]
        lines = [
            f"• **{s.get('name', 'Unknown')}** ({s.get('roll_number', '')}): **{s.get('attendance_percentage', 0)}%**"
            for s in data[:10]
        ]
        return (
            f"Student attendance ranking by lowest attendance:\n\n" + "\n".join(lines) +
            f"\n\n**{lowest.get('name', 'Unknown')}** currently has the lowest attendance at "
            f"**{lowest.get('attendance_percentage', 0)}%**."
        )
    if tool_used == "get_class_students":
        if not data:
            return "I couldn't find that class."
        students = data.get("students", [])
        if not students:
            return f"**{data.get('class_name', '')}** currently has **0 students**."
        lines = [f"• {s.get('name', 'Unknown')} ({s.get('roll_number', '')})" for s in students]
        return f"**{data.get('class_name', '')}** has **{len(students)} students**:\n\n" + "\n".join(lines)
    if tool_used == "get_total_student_count":
        return f"You currently have **{data.get('total_students', 0)}** active students."
    if tool_used == "get_classes_and_subjects":
        classes = data.get("classes", []) or []
        subjects = data.get("subjects", []) or []
        class_names = [c.get("name", "Unnamed") for c in classes]
        subject_names = [s.get("name", "Unnamed") for s in subjects]
        return (
            f"Your classes ({len(class_names)}):\n\n" + "\n".join(f"• {n}" for n in class_names) +
            f"\n\nYour subjects ({len(subject_names)}):\n\n" + "\n".join(f"• {n}" for n in subject_names)
        )
    return "I couldn't retrieve that information right now. Please try again."


async def process_message(message: str, teacher_id: str) -> dict:
    route = await _route_tool(message, teacher_id)
    tool_used = route.get("tool_used")
    data = route.get("data")

    if tool_used is None and data is None:
        answer = await _fallback_answers(message)
        return {
            "answer": answer,
            "message": answer,
            "data": None,
            "tool_used": None,
        }

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + TOOL_DESCRIPTIONS},
        {"role": "user", "content": message},
        {"role": "assistant", "content": f"Data retrieved by {tool_used}: {json.dumps(data, default=str)[:2000]}"},
    ]

    answer = await llm_client.chat(messages)

    if answer == "AI service is currently unavailable.":
        # The model backend is offline. We must NOT pretend the AI produced an
        # answer. Flag unavailability and give a clearly-labeled summary built
        # directly from the (correctly routed) tool data instead of guessing.
        summary = await _fallback_tool_message(tool_used, data)
        answer = (
            "The AI Assistant is temporarily unavailable because the AI service "
            "is not connected, so I can only show you the data directly:\n\n"
            + summary
        )
        ai_unavailable = True
    else:
        ai_unavailable = False

    return {
        "answer": answer,
        "message": answer,
        "data": data,
        "tool_used": tool_used,
        "ai_unavailable": ai_unavailable,
    }