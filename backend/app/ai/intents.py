"""Structured intent detection for the AI assistant.

The assistant routes on a small, typed intent model instead of free-form
keyword soup. Keyword routing still exists in the assistant service for
backwards compatibility, but every *supported* intent from the spec has a
structured representation here:

- attendance_summary / list_x / comparisons / thresholds / single-date queries
- export_attendance with format/date/range/class/subject filters

Date parsing follows the Indian DD/MM/YYYY convention for ambiguous numeric
dates while always honoring natural-language dates ("September 11 2026").
"""

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

MONTH_NAMES = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12,
}
# Short month names so "Sep", "Sept", "Dec" also parse.
SHORT_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7,
    "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}
_MONTH_WORDS = "|".join(list(MONTH_NAMES.keys()) + list(SHORT_MONTHS.keys()))


@dataclass
class Intent:
    intent: str
    format: Optional[str] = None          # xlsx | csv
    date: Optional[str] = None            # single date YYYY-MM-DD
    start_date: Optional[str] = None      # YYYY-MM-DD
    end_date: Optional[str] = None        # YYYY-MM-DD
    month: Optional[str] = None           # YYYY-MM
    class_id: Optional[str] = None
    subject_id: Optional[str] = None
    student_id: Optional[str] = None
    raw_scope: dict = field(default_factory=dict)


def _year(y: int) -> int:
    return 2000 + y if y < 100 else y


def _try_parts(day: int, month: int, year: int) -> Optional[str]:
    try:
        return datetime(year, month, day).strftime("%Y-%m-%d")
    except ValueError:
        return None


def parse_explicit_date(text: str) -> Optional[str]:
    """Parse an explicit date from a message.

    Numeric dates are interpreted with the Indian DD/MM/YYYY convention
    (day first). Natural-language dates always win.
    """
    low = text.lower()

    # 1) Natural language, day-before-month: "11 September 2026", "Sept 11".
    m = re.search(
        rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({_MONTH_WORDS})[a-z]*\s*(\d{{2,4}})?\b", low
    )
    if m:
        day, month_name, year_text = int(m.group(1)), m.group(2), m.group(3)
        month = MONTH_NAMES.get(month_name) or SHORT_MONTHS.get(month_name)
        year = _year(int(year_text)) if year_text else datetime.now(timezone.utc).year
        result = _try_parts(day, month, year)
        if result:
            return result

    # 2) Natural language, month-before-day: "September 11 2026".
    m = re.search(
        rf"\b({_MONTH_WORDS})[a-z]*\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:,\s*(\d{{2,4}}))?\b", low
    )
    if m:
        month_name, day, year_text = m.group(1), int(m.group(2)), m.group(3)
        month = MONTH_NAMES.get(month_name) or SHORT_MONTHS.get(month_name)
        year = _year(int(year_text)) if year_text else datetime.now(timezone.utc).year
        result = _try_parts(day, month, year)
        if result:
            return result

    # 3) Numeric date. Indian convention: day/month/year first.
    m = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b", low)
    if m:
        a, b, year_text = int(m.group(1)), int(m.group(2)), _year(int(m.group(3)))
        result = _try_parts(a, b, year_text)          # DD/MM/YYYY
        if result:
            return result
        result = _try_parts(b, a, year_text)          # MM/DD/YYYY fallback
        if result:
            return result

    return None


def parse_month(text: str) -> Optional[str]:
    """Parse a month reference: 'September', 'September 2026', '09/2026'."""
    low = text.lower()

    m = re.search(rf"\b({_MONTH_WORDS})[a-z]*\s*(\d{{4}})?\b", low)
    if m:
        month_name, year_text = m.group(1), m.group(2)
        month = MONTH_NAMES.get(month_name) or SHORT_MONTHS.get(month_name)
        year = _year(int(year_text)) if year_text else datetime.now(timezone.utc).year
        return f"{year:04d}-{month:02d}"

    m = re.search(r"\b(\d{1,2})[/-](\d{4})\b", low)
    if m:
        a, year_text = int(m.group(1)), _year(int(m.group(2)))
        if 1 <= a <= 12:
            return f"{year_text:04d}-{a:02d}"

    return None


def relative_day(text: str) -> Optional[str]:
    low = text.lower()
    today = datetime.now(timezone.utc).date()
    if re.search(r"\btoday\b|\btoday\'?s\b", low):
        return today.strftime("%Y-%m-%d")
    if re.search(r"\byesterday\b", low):
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")
    return None


def date_scope(text: str) -> dict:
    """Return a structured date scope for a message.

    One of:
      {"date": "YYYY-MM-DD"}
      {"start_date": "...", "end_date": "..."}
      {"month": "YYYY-MM"}
      {}
    """
    relative = relative_day(text)
    explicit = parse_explicit_date(text)
    month = parse_month(text)

    # Relative ("today") beats everything for daily semantics.
    if relative and not explicit:
        return {"date": relative}

    if explicit and month == explicit[:7]:
        return {"date": explicit}

    if explicit:
        return {"date": explicit}

    if month:
        return {"month": month}

    return {}


def detect_export(message: str) -> Intent:
    """Build an export intent when the message requests a file.

    Returns an Intent with intent="export_attendance" and parsed parameters,
    or None when the message is not an export request.
    """
    low = message.lower()

    has_format = any(f in low for f in ["excel", "xlsx", "xls", "csv", "spreadsheet", " spreadsheet"])
    has_file_word = any(f in low for f in [" sheet", "excel", "csv", "xlsx", "spreadsheet"])
    has_verb = any(
        v in low for v in
        ["export", "download", "generate", "create", "make", "prepare", "produce"]
    )
    mentions_attendance = "attendance" in low or "report" in low or has_file_word

    if not mentions_attendance or not (has_verb or has_format):
        return None

    scope = date_scope(low)
    fmt = "csv" if "csv" in low else ("xlsx" if has_format else "xlsx")

    return Intent(
        intent="export_attendance",
        format=fmt,
        date=scope.get("date"),
        start_date=scope.get("start_date"),
        end_date=scope.get("end_date"),
        month=scope.get("month"),
    )