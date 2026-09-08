from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from typing import Optional
from app.services import export_service
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/exports", tags=["Exports"])


@router.get("/attendance/csv")
async def export_csv(
    class_id: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    filepath = await export_service.export_attendance_csv(
        class_id=class_id, from_date=from_date, to_date=to_date
    )
    if not filepath:
        return {"success": True, "data": {"message": "No data to export"}}
    return FileResponse(
        path=filepath,
        filename=filepath.split("/")[-1],
        media_type="text/csv",
    )


@router.get("/attendance/excel")
async def export_excel(
    class_id: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    filepath = await export_service.export_attendance_excel(
        class_id=class_id, from_date=from_date, to_date=to_date
    )
    if not filepath:
        return {"success": True, "data": {"message": "No data to export"}}
    return FileResponse(
        path=filepath,
        filename=filepath.split("/")[-1],
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
