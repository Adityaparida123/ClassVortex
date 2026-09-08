from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from app.schemas.attendance import (
    AttendanceSessionCreate,
    AttendanceRecordCreate,
    AttendanceRecordBulk,
    AttendanceRecordUpdate,
)
from app.services import attendance_service
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/attendance", tags=["Attendance"])


@router.post("/sessions", response_model=dict)
async def create_session(
    request: AttendanceSessionCreate,
    current_user: dict = Depends(get_current_user),
):
    session = await attendance_service.create_session(
        request.model_dump(), teacher_id=str(current_user["_id"])
    )
    return {"success": True, "data": session}


@router.get("/sessions", response_model=dict)
async def list_sessions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    class_id: Optional[str] = None,
    subject_id: Optional[str] = None,
    date: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    sessions, total = await attendance_service.get_sessions(
        page=page, limit=limit, class_id=class_id,
        subject_id=subject_id, date=date,
    )
    return {
        "success": True,
        "data": sessions,
        "pagination": {"page": page, "limit": limit, "total": total},
    }


@router.get("/sessions/{session_id}", response_model=dict)
async def get_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    session = await attendance_service.get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    records = await attendance_service.get_records_by_session(session_id)
    return {"success": True, "data": {"session": session, "records": records}}


@router.post("/sessions/{session_id}/records", response_model=dict)
async def create_record(
    session_id: str,
    request: AttendanceRecordCreate,
    current_user: dict = Depends(get_current_user),
):
    try:
        record = await attendance_service.create_record(
            session_id, request.student_id, request.status
        )
        return {"success": True, "data": record}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/sessions/{session_id}/bulk", response_model=dict)
async def bulk_mark_attendance(
    session_id: str,
    request: AttendanceRecordBulk,
    current_user: dict = Depends(get_current_user),
):
    session = await attendance_service.get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    records = await attendance_service.bulk_create_records(
        session_id, [r.model_dump() for r in request.records]
    )
    return {"success": True, "data": records}


@router.put("/records/{record_id}", response_model=dict)
async def update_record(
    record_id: str,
    request: AttendanceRecordUpdate,
    current_user: dict = Depends(get_current_user),
):
    record = await attendance_service.update_record(record_id, request.status)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return {"success": True, "data": record}


@router.get("/student/{student_id}", response_model=dict)
async def get_student_attendance(
    student_id: str,
    current_user: dict = Depends(get_current_user),
):
    records = await attendance_service.get_records_by_student(student_id)
    return {"success": True, "data": records}


@router.get("/student/{student_id}/summary", response_model=dict)
async def get_student_summary(
    student_id: str,
    current_user: dict = Depends(get_current_user),
):
    summary = await attendance_service.get_student_summary(student_id)
    return {"success": True, "data": summary}


@router.get("/class/{class_id}", response_model=dict)
async def get_class_attendance(
    class_id: str,
    date: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    records = await attendance_service.get_records_by_class(class_id, date)
    return {"success": True, "data": records}
