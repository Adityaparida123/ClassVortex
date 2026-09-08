from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from app.schemas.student import StudentCreate, StudentUpdate, StudentResponse
from app.services import student_service
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/students", tags=["Students"])


@router.post("", response_model=dict)
async def create_student(
    request: StudentCreate,
    current_user: dict = Depends(get_current_user),
):
    try:
        student = await student_service.create_student(request.model_dump())
        return {"success": True, "data": student}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("", response_model=dict)
async def list_students(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    class_id: Optional[str] = None,
    semester: Optional[int] = None,
    section: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    students, total = await student_service.get_students(
        page=page, limit=limit, class_id=class_id,
        semester=semester, section=section, search=search,
    )
    return {
        "success": True,
        "data": students,
        "pagination": {"page": page, "limit": limit, "total": total},
    }


@router.get("/{student_id}", response_model=dict)
async def get_student(
    student_id: str,
    current_user: dict = Depends(get_current_user),
):
    student = await student_service.get_student_by_id(student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return {"success": True, "data": student}


@router.put("/{student_id}", response_model=dict)
async def update_student(
    student_id: str,
    request: StudentUpdate,
    current_user: dict = Depends(get_current_user),
):
    student = await student_service.update_student(student_id, request.model_dump(exclude_unset=True))
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return {"success": True, "data": student}


@router.delete("/{student_id}", response_model=dict)
async def delete_student(
    student_id: str,
    current_user: dict = Depends(get_current_user),
):
    deleted = await student_service.delete_student(student_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return {"success": True, "data": {"message": "Student deleted"}}
