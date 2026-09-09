import json
import re
from app.ai.llm_client import llm_client
from app.ai.prompts import SYSTEM_PROMPT, TOOL_DESCRIPTIONS
from app.ai import tools


async def process_message(message: str, teacher_id: str) -> dict:
    tool_used = None
    data = None

    message_lower = message.lower()

    # 1. Check for student-specific queries (e.g. "What is Rahul's attendance?")
    st_info = await tools.find_student_attendance(message, teacher_id)
    if st_info:
        tool_used = "find_student_attendance"
        data = st_info
    elif any(phrase in message_lower for phrase in ["below 75", "less than 75", "low attendance", "lowest attendance"]):
        tool_used = "get_low_attendance_students"
        data = await tools.get_low_attendance_students(75.0, teacher_id)
    elif any(phrase in message_lower for phrase in ["absent", "who is absent", "not present"]):
        tool_used = "get_absent_students"
        data = await tools.get_absent_students(teacher_id)
    elif "monthly" in message_lower and "report" in message_lower:
        tool_used = "get_monthly_report"
        data = await tools.get_monthly_report("", teacher_id)
    elif "student" in message_lower and any(c.isdigit() for c in message):
        match = re.search(r'[a-f0-9]{24}', message)
        if match:
            tool_used = "get_student_attendance"
            data = await tools.get_student_attendance(match.group(), teacher_id)

    if data is None and tool_used is None:
        data = await tools.get_low_attendance_students(75.0, teacher_id)
        tool_used = "get_low_attendance_students"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + TOOL_DESCRIPTIONS},
        {"role": "user", "content": message},
        {"role": "assistant", "content": f"Data retrieved: {json.dumps(data, default=str)[:500]}"},
    ]

    answer = await llm_client.chat(messages)

    if answer == "AI service is currently unavailable.":
        if tool_used == "find_student_attendance" and isinstance(data, dict):
            st = data.get("student", {})
            name = st.get("name", "Student")
            roll = st.get("roll_number", "")
            pct = data.get("percentage", 0)
            tot = data.get("total", 0)
            pres = data.get("present", 0)
            answer = f"**{name}** ({roll}): Attendance is **{pct}%** ({pres} present out of {tot} total sessions)."
        elif tool_used == "get_low_attendance_students" and isinstance(data, list):
            if len(data) == 0:
                answer = "All active students currently have attendance of **75% or higher**."
            else:
                lines = [f"• **{s['name']}** ({s.get('roll_number', '')}): **{s.get('attendance_percentage', 0)}%** ({s.get('present_sessions', 0)}/{s.get('total_sessions', 0)} sessions)" for s in data]
                answer = f"Found **{len(data)} student(s)** with attendance below 75%:\n\n" + "\n".join(lines)
        elif tool_used == "get_absent_students" and isinstance(data, list):
            if len(data) == 0:
                answer = "No absent student records found."
            else:
                names = list({s.get("student_name") for s in data if s.get("student_name")})
                if names:
                    answer = f"Recent absent students ({len(names)}):\n\n" + "\n".join(f"• {name}" for name in names)
                else:
                    answer = f"Found **{len(data)} absent records**."
        elif tool_used == "get_monthly_report" and isinstance(data, dict):
            answer = f"**Monthly Report ({data.get('month', '')})**: Total **{data.get('total_sessions', 0)} sessions** recorded."
        elif isinstance(data, list):
            answer = f"Retrieved {len(data)} attendance records."
        elif isinstance(data, dict):
            answer = f"Data: {json.dumps(data, default=str)[:500]}"

    return {"answer": answer, "message": answer, "data": data, "tool_used": tool_used}
