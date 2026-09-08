import re
import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger("attendvortex.sheets")

SHEETS_URL_RE = re.compile(
    r"https://docs\.google\.com/spreadsheets/d/([A-Za-z0-9_-]+)"
)

NAME_ALIASES = {
    "name", "student name", "full name", "student_name", "student",
}
REG_ALIASES = {
    "registration number", "registration no", "registration no.",
    "registration_number", "reg no", "reg no.", "roll no", "roll number",
    "enrollment number", "enrollment no", "enrollment_number",
}
EMAIL_ALIASES = {
    "email", "email address", "e-mail", "student email", "student_email",
}

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
MAX_NAME_LEN = 200
MAX_ROWS = 2000


def extract_spreadsheet_id(url: str) -> Optional[str]:
    m = SHEETS_URL_RE.match(url.strip())
    return m.group(1) if m else None


def is_google_sheets_url(url: str) -> bool:
    return bool(SHEETS_URL_RE.match(url.strip()))


def _normalize_header(h: str) -> str:
    h = h.lower().strip()
    h = re.sub(r"[.\-]+", " ", h)
    h = re.sub(r"\s+", " ", h).strip()
    return h


def detect_columns(headers: list[str]) -> dict:
    mapping: dict[str, Optional[int]] = {
        "name": None,
        "registration_number": None,
        "email": None,
    }
    normalized = [_normalize_header(h) for h in headers]
    for idx, norm in enumerate(normalized):
        if mapping["name"] is None and norm in NAME_ALIASES:
            mapping["name"] = idx
        if mapping["registration_number"] is None and norm in REG_ALIASES:
            mapping["registration_number"] = idx
        if mapping["email"] is None and norm in EMAIL_ALIASES:
            mapping["email"] = idx
    return mapping


def validate_row(
    row: list[str],
    col_map: dict,
    row_num: int,
    seen_rolls: set[str],
    seen_emails: set[str],
    existing_rolls: set[str],
    existing_emails: set[str],
) -> dict:
    def get(field: str) -> str:
        idx = col_map.get(field)
        if idx is None or idx >= len(row):
            return ""
        return str(row[idx]).strip()

    name = get("name")
    reg = get("registration_number")
    email = get("email").lower()

    issues: list[str] = []

    if not name:
        issues.append("Missing name")
    elif len(name) > MAX_NAME_LEN:
        issues.append("Name too long")

    if not reg:
        issues.append("Missing registration number")

    if not email:
        issues.append("Missing email")
    elif not EMAIL_RE.match(email):
        issues.append("Invalid email")

    if not issues:
        if reg in existing_rolls:
            issues.append("Duplicate registration number")
        elif reg in seen_rolls:
            issues.append("Duplicate registration number in sheet")

        if email and email in existing_emails:
            if "Duplicate registration number" not in issues:
                issues.append("Duplicate email")
        elif email and email in seen_emails:
            if "Duplicate registration number" not in issues:
                issues.append("Duplicate email in sheet")

    valid = len(issues) == 0

    if valid:
        seen_rolls.add(reg)
        seen_emails.add(email)

    status = "Ready" if valid else ", ".join(issues)

    return {
        "row": row_num,
        "name": name,
        "registration_number": reg,
        "email": email,
        "status": status,
        "valid": valid,
    }


def parse_rows(
    headers: list[str],
    rows: list[list[str]],
    col_map: dict,
    existing_rolls: set[str],
    existing_emails: set[str],
) -> list[dict]:
    seen_rolls: set[str] = set()
    seen_emails: set[str] = set()
    results = []
    for i, row in enumerate(rows[:MAX_ROWS], start=2):
        if all(cell.strip() == "" for cell in row):
            continue
        results.append(
            validate_row(
                row, col_map, i,
                seen_rolls, seen_emails,
                existing_rolls, existing_emails,
            )
        )
    return results


def _build_gspread_client():
    import gspread
    from google.oauth2.service_account import Credentials
    import json
    import os

    sa_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if sa_json:
        info = json.loads(sa_json)
        creds = Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
        )
    else:
        sa_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "")
        if not sa_file:
            raise RuntimeError(
                "Google Sheets credentials not configured. "
                "Set GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_SERVICE_ACCOUNT_FILE."
            )
        creds = Credentials.from_service_account_file(
            sa_file,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
        )
    return gspread.authorize(creds)


def _fetch_via_gspread(spreadsheet_id: str) -> tuple[str, str, list[str], list[list[str]]]:
    gc = _build_gspread_client()
    try:
        sh = gc.open_by_key(spreadsheet_id)
    except Exception as exc:
        msg = str(exc).lower()
        if "not found" in msg or "404" in msg:
            raise ValueError("Spreadsheet not found. Check the URL and try again.")
        if "permission" in msg or "403" in msg or "access" in msg:
            raise PermissionError(
                "Cannot access this spreadsheet. Make sure it is shared with your "
                "Google service account or set to 'Anyone with the link can view'."
            )
        raise ValueError(f"Google Sheets error: {exc}")

    worksheet = sh.sheet1
    title = sh.title
    sheet_name = worksheet.title
    all_values = worksheet.get_all_values()
    if not all_values:
        raise ValueError("The spreadsheet is empty.")
    headers = all_values[0]
    rows = all_values[1:]
    return title, sheet_name, headers, rows


def _fetch_public_csv(spreadsheet_id: str) -> tuple[str, str, list[str], list[list[str]]]:
    import csv
    import io
    import urllib.request

    export_url = (
        f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        f"/export?format=csv&gid=0"
    )
    try:
        with urllib.request.urlopen(export_url, timeout=15) as resp:
            if resp.status != 200:
                raise ValueError(f"HTTP {resp.status}")
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" in content_type:
                raise PermissionError(
                    "This spreadsheet is not publicly accessible. "
                    "Either make it 'Anyone with the link can view' "
                    "or configure a Google Service Account."
                )
            raw = resp.read().decode("utf-8-sig")
    except PermissionError:
        raise
    except Exception as exc:
        raise ValueError(f"Could not fetch spreadsheet: {exc}")

    reader = csv.reader(io.StringIO(raw))
    all_rows = list(reader)
    if not all_rows:
        raise ValueError("The spreadsheet is empty.")
    headers = all_rows[0]
    rows = all_rows[1:]
    return "Spreadsheet", "Sheet1", headers, rows


def fetch_sheet_data(spreadsheet_id: str) -> tuple[str, str, list[str], list[list[str]]]:
    import os
    has_credentials = bool(
        os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON") or
        os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    )
    if has_credentials:
        try:
            return _fetch_via_gspread(spreadsheet_id)
        except (ValueError, PermissionError):
            raise
        except Exception as exc:
            logger.warning("gspread failed, trying public CSV: %s", exc)

    return _fetch_public_csv(spreadsheet_id)
