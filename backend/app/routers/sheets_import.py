from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from app.core.dependencies import get_current_admin_user
from app.services import sheets_service
from app.services import student_service
from app.database import get_database

router = APIRouter(prefix="/api/v1/students/import/google-sheets", tags=["Students Import"])


class AnalyzeRequest(BaseModel):
    url: str


class ColumnMapping(BaseModel):
    name: Optional[str] = None
    registration_number: Optional[str] = None
    email: Optional[str] = None


class ConfirmRequest(BaseModel):
    spreadsheet_id: str
    sheet_name: str
    column_mapping: ColumnMapping
    rows: list[dict]


class ImportSummary(BaseModel):
    imported: int
    skipped_duplicates: int
    invalid: int
    details: list[dict]


@router.post("/analyze")
async def analyze_sheet(
    request: AnalyzeRequest,
    current_user: dict = Depends(get_current_admin_user),
):
    if not sheets_service.is_google_sheets_url(request.url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Google Sheets URL. Expected format: https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit",
        )

    spreadsheet_id = sheets_service.extract_spreadsheet_id(request.url)
    if not spreadsheet_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract spreadsheet ID from URL.",
        )

    try:
        title, sheet_name, headers, rows = sheets_service.fetch_sheet_data(spreadsheet_id)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch spreadsheet: {exc}",
        )

    col_map = sheets_service.detect_columns(headers)
    auto_detected = all(v is not None for v in col_map.values())

    db = get_database()
    cursor = db.students.find(
        {"teacher_id": str(current_user["_id"])}, {"roll_number": 1, "email": 1}
    )
    existing_rolls: set[str] = set()
    existing_emails: set[str] = set()
    async for doc in cursor:
        if doc.get("roll_number"):
            existing_rolls.add(doc["roll_number"])
        if doc.get("email"):
            existing_emails.add(doc["email"].lower())

    preview = sheets_service.parse_rows(
        headers, rows, col_map, existing_rolls, existing_emails
    )

    total_rows = len(rows)
    valid_count = sum(1 for r in preview if r["valid"])
    duplicate_count = sum(
        1 for r in preview
        if not r["valid"] and ("Duplicate" in r["status"] or "duplicate" in r["status"])
    )
    invalid_count = sum(1 for r in preview if not r["valid"] and "Duplicate" not in r["status"])

    return {
        "success": True,
        "data": {
            "spreadsheet_title": title,
            "sheet_name": sheet_name,
            "spreadsheet_id": spreadsheet_id,
            "headers": headers,
            "total_rows": total_rows,
            "auto_detected": auto_detected,
            "column_mapping": {
                k: (headers[v] if v is not None else None)
                for k, v in col_map.items()
            },
            "preview": preview,
            "summary": {
                "total": total_rows,
                "ready": valid_count,
                "duplicates": duplicate_count,
                "invalid": invalid_count,
            },
        },
    }


@router.post("/confirm")
async def confirm_import(
    request: ConfirmRequest,
    current_user: dict = Depends(get_current_admin_user),
):
    if not request.rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No rows to import.",
        )

    col_map: dict[str, Optional[int]] = {
        "name": None,
        "registration_number": None,
        "email": None,
    }
    mapping = request.column_mapping
    if mapping.name is not None:
        col_map["name"] = request.headers.index(mapping.name) if mapping.name in request.headers else None
    if mapping.registration_number is not None:
        col_map["registration_number"] = request.headers.index(mapping.registration_number) if mapping.registration_number in request.headers else None
    if mapping.email is not None:
        col_map["email"] = request.headers.index(mapping.email) if mapping.email in request.headers else None

    if None in col_map.values():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All three columns (name, registration_number, email) must be mapped.",
        )

    db = get_database()
    cursor = db.students.find(
        {"teacher_id": str(current_user["_id"])}, {"roll_number": 1, "email": 1}
    )
    existing_rolls: set[str] = set()
    existing_emails: set[str] = set()
    async for doc in cursor:
        if doc.get("roll_number"):
            existing_rolls.add(doc["roll_number"])
        if doc.get("email"):
            existing_emails.add(doc["email"].lower())

    preview = sheets_service.parse_rows(
        request.headers, request.rows, col_map, existing_rolls, existing_emails
    )

    valid_rows = [r for r in preview if r["valid"]]

    if not valid_rows:
        return {
            "success": True,
            "data": ImportSummary(
                imported=0,
                skipped_duplicates=0,
                invalid=len(preview),
                details=[{"row": r["row"], "reason": r["status"]} for r in preview if not r["valid"]],
            ).model_dump(),
        }

    docs_to_insert = []
    for r in valid_rows:
        docs_to_insert.append({
            "name": r["name"],
            "roll_number": r["registration_number"],
            "email": r["email"],
            "phone": "",
            "class_id": "unassigned",
            "teacher_id": str(current_user["_id"]),
            "semester": 1,
            "section": "A",
            "is_active": True,
        })

    if docs_to_insert:
        result = await db.students.insert_many(docs_to_insert)
        imported = len(result.inserted_ids)
    else:
        imported = 0

    skipped_duplicates = sum(
        1 for r in preview
        if not r["valid"] and ("Duplicate" in r["status"] or "duplicate" in r["status"])
    )
    invalid = sum(
        1 for r in preview
        if not r["valid"] and "Duplicate" not in r["status"]
    )

    details = []
    for r in preview:
        if not r["valid"]:
            details.append({"row": r["row"], "reason": r["status"]})

    return {
        "success": True,
        "data": ImportSummary(
            imported=imported,
            skipped_duplicates=skipped_duplicates,
            invalid=invalid,
            details=details,
        ).model_dump(),
    }