import json
import re
from app.ai.llm_client import llm_client
from app.ai.prompts import SYSTEM_PROMPT, TOOL_DESCRIPTIONS
from app.ai import tools


async def process_message(message: str) -> dict:
    tool_used = None
    data = None

    message_lower = message.lower()

    if any(phrase in message_lower for phrase in ["below 75", "less than 75", "low attendance"]):
        tool_used = "get_low_attendance_students"
        data = await tools.get_low_attendance_students(75.0)
    elif any(phrase in message_lower for phrase in ["absent", "who is absent", "not present"]):
        tool_used = "get_absent_students"
        data = await tools.get_absent_students()
    elif "monthly" in message_lower and "report" in message_lower:
        tool_used = "get_monthly_report"
        data = await tools.get_monthly_report()
    elif "student" in message_lower and any(c.isdigit() for c in message):
        match = re.search(r'[a-f0-9]{24}', message)
        if match:
            tool_used = "get_student_attendance"
            data = await tools.get_student_attendance(match.group())

    if data is None and tool_used is None:
        data = await tools.get_low_attendance_students(75.0)
        tool_used = "get_low_attendance_students"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + TOOL_DESCRIPTIONS},
        {"role": "user", "content": message},
        {"role": "assistant", "content": f"Data retrieved: {json.dumps(data, default=str)[:500]}"},
    ]

    answer = await llm_client.chat(messages)

    if answer == "AI service is currently unavailable.":
        if isinstance(data, list):
            answer = f"Found {len(data)} records. (AI summarization unavailable)"
        elif isinstance(data, dict):
            answer = f"Data: {json.dumps(data, default=str)[:500]}. (AI summarization unavailable)"

    return {"answer": answer, "data": data, "tool_used": tool_used}
