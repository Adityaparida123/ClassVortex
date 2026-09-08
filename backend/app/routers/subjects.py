from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectResponse
from app.services import subject_service
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/subjects", tags=["Subjects"])


@router.post("", response_model=dict)
async def create_subject(
    request: SubjectCreate,
    current_user: dict = Depends(get_current_user),
):
    try:
        subject = await subject_service.create_subject(request.model_dump())
        return {"success": True, "data": subject}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("", response_model=dict)
async def list_subjects(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    class_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    subjects, total = await subject_service.get_subjects(page=page, limit=limit, class_id=class_id)
    return {
        "success": True,
        "data": subjects,
        "pagination": {"page": page, "limit": limit, "total": total},
    }


@router.get("/{subject_id}", response_model=dict)
async def get_subject(
    subject_id: str,
    current_user: dict = Depends(get_current_user),
):
    subject = await subject_service.get_subject_by_id(subject_id)
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    return {"success": True, "data": subject}


@router.put("/{subject_id}", response_model=dict)
async def update_subject(
    subject_id: str,
    request: SubjectUpdate,
    current_user: dict = Depends(get_current_user),
):
    subject = await subject_service.update_subject(subject_id, request.model_dump(exclude_unset=True))
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    return {"success": True, "data": subject}


@router.delete("/{subject_id}", response_model=dict)
async def delete_subject(
    subject_id: str,
    current_user: dict = Depends(get_current_user),
):
    deleted = await subject_service.delete_subject(subject_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    return {"success": True, "data": {"message": "Subject deleted"}}
