from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.schemas.class_schema import ClassCreate, ClassUpdate, ClassResponse
from app.services import class_service
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/classes", tags=["Classes"])


@router.post("", response_model=dict)
async def create_class(
    request: ClassCreate,
    current_user: dict = Depends(get_current_user),
):
    cls = await class_service.create_class(request.model_dump())
    return {"success": True, "data": cls}


@router.get("", response_model=dict)
async def list_classes(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    classes, total = await class_service.get_classes(page=page, limit=limit)
    return {
        "success": True,
        "data": classes,
        "pagination": {"page": page, "limit": limit, "total": total},
    }


@router.get("/{class_id}", response_model=dict)
async def get_class(
    class_id: str,
    current_user: dict = Depends(get_current_user),
):
    cls = await class_service.get_class_by_id(class_id)
    if not cls:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return {"success": True, "data": cls}


@router.put("/{class_id}", response_model=dict)
async def update_class(
    class_id: str,
    request: ClassUpdate,
    current_user: dict = Depends(get_current_user),
):
    cls = await class_service.update_class(class_id, request.model_dump(exclude_unset=True))
    if not cls:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return {"success": True, "data": cls}


@router.delete("/{class_id}", response_model=dict)
async def delete_class(
    class_id: str,
    current_user: dict = Depends(get_current_user),
):
    deleted = await class_service.delete_class(class_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return {"success": True, "data": {"message": "Class deleted"}}
