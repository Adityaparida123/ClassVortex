from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from app.services import report_service
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


@router.get("/dashboard", response_model=dict)
async def dashboard_summary(
    current_user: dict = Depends(get_current_user),
):
    """Teacher-scoped control-center summary for the dashboard."""
    report = await report_service.get_dashboard_summary(str(current_user["_id"]))
    return {"success": True, "data": report}


@router.get("/daily", response_model=dict)
async def daily_report(
    class_id: Optional[str] = None,
    date: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    report = await report_service.get_daily_report(
        str(current_user["_id"]), class_id=class_id, date=date
    )
    return {"success": True, "data": report}


@router.get("/monthly", response_model=dict)
async def monthly_report(
    class_id: Optional[str] = None,
    month: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    report = await report_service.get_monthly_report(
        str(current_user["_id"]), class_id=class_id, month=month
    )
    return {"success": True, "data": report}


@router.get("/student/{student_id}", response_model=dict)
async def student_report(
    student_id: str,
    current_user: dict = Depends(get_current_user),
):
    report = await report_service.get_student_report(str(current_user["_id"]), student_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return {"success": True, "data": report}


@router.get("/class/{class_id}", response_model=dict)
async def class_report(
    class_id: str,
    current_user: dict = Depends(get_current_user),
):
    report = await report_service.get_class_report(str(current_user["_id"]), class_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return {"success": True, "data": report}